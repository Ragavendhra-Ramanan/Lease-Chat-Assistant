from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from db.vectordb_operations import connection_to_wcs, close_connection
from utils.secrets import weaviate_api_key, weaviate_url, openai_api_key, mongo_uri
from models.conversation_request import ConversationResponse, ConversationRequest, Message, StartConversation, conversation_helper
from router.nodes.router_node import RouteNode
from models.agent_state import AgentState
from uuid import uuid4
from typing import Dict
from utils.flows import ROUTE_MAP
from utils.helper_functions import get_data, filter_df
from models.auth_models import User, SignupResponse, Login, LoginResponse
from fastapi.middleware.cors import CORSMiddleware
from memory.memory_store import get_recent_memory, add_short_term_memory_from_dict
from decomposition.nodes.decomposition_node import DecompositionNode
from decomposition.nodes.decomposition_result_node import DecompositionResultNode
from utils.helper_functions import USER_CSV_FILE, load_user_data

import pandas as pd 
from datetime import datetime
from collections import Counter
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

origins = [
    "http://localhost:4200",  # frontend URL
    "http://127.0.0.1:4200",  # optional
]


client = None
router = RouteNode()
decomposition = DecompositionNode()
decomposition_result = DecompositionResultNode()
vehicle_df, product_df,contract_df = get_data()
quote_filtering_node = ROUTE_MAP["filtering"](vehicle_df, product_df, filter_df)
quote_update_node = ROUTE_MAP["quote_field_update"]()
quote_generate_node = ROUTE_MAP["quote"]()

message_buffer: List[ConversationResponse] = []
MAX_BATCH_SIZE = 20
buffer_lock = asyncio.Lock()

# Initialize in main.py
conversations: Dict[str, Dict[str, any]] = {}
def get_client_state(user_id: str) -> AgentState:
    if user_id not in conversations:
        conversations[user_id] = AgentState()
    return conversations[user_id]

def save_client_state(user_id: str, state: AgentState):
    conversations[user_id] = state

def get_last_query(user_id: str) -> str:
    """
    Returns the last user query from memory, or empty string if none.
    """
    recent_memory = get_recent_memory(user_id)
    if not recent_memory:
        return ""
    return recent_memory[-1]["query"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    global conversations_collection
    # startup
    client = connection_to_wcs(weaviate_url=weaviate_url,
                               weaviate_api_key=weaviate_api_key,
                               openai_api_key=openai_api_key)
    
    # MongoDB setup
    mongo_client = AsyncIOMotorClient(mongo_uri)
    db = mongo_client["chat_db"]
    conversations_collection = db["conversations"]
    flush_task = asyncio.create_task(periodic_flush_task())
    
    try:
        yield
    finally:
        # Optionally flush remaining messages before shutdown
        async with buffer_lock:
            if message_buffer:
                await flush_buffer_to_db()

        # shutdown
        mongo_client.close()
        close_connection(client=client)
        flush_task.cancel()        
        try:
            await flush_task
        except asyncio.CancelledError:
            print("[Shutdown] Flush task cancelled cleanly.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # allow specific origins
    allow_credentials=True,
    allow_methods=["*"],             # allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)
load_user_data()
@app.post("/api/auth/signup")
async def signup_user(user:User):
    df = pd.read_csv(USER_CSV_FILE)

    # Check for duplicate email/mobile
    if ((df["email"] == user.email).any()) or ((df["mobile"] == user.mobile).any()):
        raise HTTPException(status_code=400, detail="User already exists")

    # Create new user with UUID
    if df.empty:
        user_id = 1000
    else:
        user_id = df["userId"].max() + 1

    new_user = {
        "userId": user_id,
        "firstName": user.firstName,
        "lastName": user.lastName,
        "email": user.email,
        "mobile": user.mobile,
        "password": user.password,
        "country": user.country
    }

    df = pd.concat([df, pd.DataFrame([new_user])], ignore_index=True)
    df.to_csv(USER_CSV_FILE, index=False)
    signup_response = SignupResponse(
        value=True
    )
    return signup_response


@app.post("/api/auth/login")
async def login_user(credentials : Login):
    df = pd.read_csv(USER_CSV_FILE)
    # Check user by email or mobile + password
    user_row = df[
        ((df["email"] == credentials.userName) | (df["mobile"] == credentials.userName)) &
        (df["password"] == credentials.password)
    ]

    if user_row.empty:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Convert row to dict and remove password
    user_data = user_row.iloc[0].to_dict()
    login_response = LoginResponse(
                userId= str(user_data['userId'])
            )
    return login_response


# GET: Retrieve all conversation by userId
@app.get("/api/chat/getConversations/{userId}", response_model=List[ConversationResponse])
async def get_conversation(userId: str):
    convo = await conversations_collection.find({"userId": userId}).to_list()
    if not convo:
        return []
    return [conversation_helper(c) for c in convo]
    

@app.post("/api/chat/startNewConversation")
async def start_conversation(request:StartConversation):
    """Start a new conversation and return conversation_id."""
    #Push all conversations to the db
    await flush_buffer_to_db()

    state = get_client_state(request.userId)
    conversation_id = str(uuid4())
    now = datetime.now().isoformat(timespec='seconds')

    welcome = Message(
        sender="bot",
        message="Hi, welcome! I will help in product search, vehicle search, contract search and quote generation",
        timestamp=now
    )

    response = ConversationResponse(
        userId= request.userId,
        conversationId=conversation_id,
        messages=[welcome]
    )    

    convo_doc = {
        "userId": request.userId,
        "conversationId": conversation_id,
        "messages": [welcome.model_dump()]
    }
    message_buffer.append(convo_doc)
    state.customer_id = request.userId
    save_client_state(request.userId, state)
    return response

@app.get("/api/chat/recommendations/{userID}")
async def recommendations(userID:int):
    return ["Toyota cars", "Flexi lease term 24 months" , "quote generation"]

@app.post("/api/chat/sendMessage")
async def decompose_tasks(request: ConversationRequest):
   
    # Check if conversation exists
    conversationId = request.conversationId
    userId = request.userId
            
    message_data = [request.messages.model_dump()] #[msg.model_dump() for msg in message.messages]
    convo_doc = {
            "userId": userId,
            "conversationId": conversationId,
            "messages": message_data
    }
    
    message_buffer.append(convo_doc)

    if len(message_buffer) >= MAX_BATCH_SIZE:
        # Flush the buffer to MongoDB
        await flush_buffer_to_db()

    context=[]
    questions = []
    query = request.messages.message
    state = get_client_state(request.userId)
    if "quotation" not in state.route:
        decomposition_values, rewritten_query = await decomposition.run(query)
        flag = False
        print("\nTasks To do\n")
        print(decomposition_values)
        for task, retriever in decomposition_values:
            if retriever: 
                flag = True
                request.messages.message = task
                task_response , query_retrieved = await get_conversation_result(request=request)
                if "quotation" in state.route:
                    return task_response
                print("\nResponse\n")
                print(state.final_answer)
                questions.append(query_retrieved)
                context.append([f"{task} : {state.final_answer}"])
            else:
                questions.append(task)
        if flag:
            if len(questions) == 0:
                questions.append(rewritten_query)
            print("\nFinal Combined result\n")      
            final_answer = await decomposition_result.run(context=context,questions=questions)
            print(final_answer)
            response = ConversationResponse(
                messages=[request.messages],              # empty list or actual messages
                userId= request.userId  ,     # string
                conversationId=request.conversationId # string
                )
                    
            now = datetime.now().isoformat(timespec='seconds')
            response.messages.append(Message(
                sender="bot",
                message=final_answer,
                timestamp=now
            ))
        else:
            response,query_retrieved= await get_conversation_result(request=request)
            questions.append(query_retrieved)
        add_short_term_memory_from_dict(user_id=request.userId,query=",".join(questions),response=response)

    else:
        response,query = await get_conversation_result(request=request)
    convo_doc = {
    "userId": request.userId,
    "conversationId": request.conversationId,
    "messages": [response.messages[-1].model_dump()]
    }
    message_buffer.append(convo_doc)
    return response
    
    
    
async def flush_buffer_to_db():
    global message_buffer
    if not message_buffer:
        return
    
    buffer_copy = message_buffer.copy()
    message_buffer.clear()

    try:
        #validation to ensure there is atleast one user message
        list_convo_id = [msg.get("conversationId") for msg in buffer_copy]
        count_convo_id = dict(Counter(list_convo_id))
        
        for msg in buffer_copy:      
            if(count_convo_id[msg.get("conversationId")]<2):
                message_buffer.append(msg)
            else:           
                await conversations_collection.update_one(
                    {
                        "userId": msg.get("userId"),
                        "conversationId": msg.get("conversationId")
                    },
                    {
                        "$push": {"messages": { "$each": msg.get("messages") }}
                    },
                    upsert=True
                )
            #print(f"Inserted {len(buffer_copy)} messages to DB.")
    except Exception as e:
        print(f"[Error] Failed to insert batch: {e}")

async def periodic_flush_task():
    while True:
        await asyncio.sleep(1*60)  # every 10mins
        async with buffer_lock:
            if message_buffer:
                await flush_buffer_to_db()

async def get_conversation_result(request: ConversationRequest):    
    query = request.messages.message
    state = get_client_state(request.userId)
    state.trace = [[]]
    state.previous_query = get_last_query(state.customer_id)
    state.query = query
    # #memory context
    # memory_text = ""
    # if is_relevant_to_memory(state.customer_id, state.query):
    #     memory_entries = get_recent_memory(state.customer_id)
    #     memory_text = "\n".join([f"User: {m['query']} | Bot: {m['response']}" for m in memory_entries])
    response = ConversationResponse(
    messages=[request.messages],              # empty list or actual messages
    userId= request.userId  ,     # string
    conversationId=request.conversationId # string
    )
    sender = "bot"
    response.conversationId = request.conversationId
    response.userId = request.userId
    if "quotation" in state.route:
        state = await quote_update_node.run(state)
        if state.quote_next_agent == "filtering":
            state = await quote_filtering_node.run(state)
            save_client_state(request.userId,state=state)            
            now = datetime.now().isoformat(timespec='seconds')
            response.messages.append(Message(
                sender=sender,
                message=state.quote_intermediate_results,
                timestamp=now
            ))
            return response,state.rewritten_query
        elif state.quote_next_agent == "quote":
            state = await quote_generate_node.run(state)
            state.route = ""
            state.quote_step = "preowned"
            state.quote_context = ""
            state.quote_next_agent = ""
            save_client_state(request.userId,state=state)            
            now = datetime.now().isoformat(timespec='seconds')
            response.messages.append(Message(
                sender=sender,
                message=state.quote_results,
                timestamp=now
            )) 
            return response,state.rewritten_query

    state = await router.run(state)
    routes = state.route
    flow_instance = None
    state.customer_id = request.userId
    print("\nCurrent task\n")
    print(state.rewritten_query)
    print(routes,"route")    
    limit = 5
    # Pick flow by checking membership
    if "quotation" in routes:
        flow_instance = quote_filtering_node
        state.quote_context = "vehicle"
    elif "contract" in routes:
        flow_instance = ROUTE_MAP["contract"](client=client,df=contract_df,limit=limit)
    elif "product" in routes:
        flow_instance = ROUTE_MAP["product"](client=client,limit=limit)
    elif "vehicle" in routes:
        flow_instance = ROUTE_MAP["vehicle"](client=client,limit=limit)
    else:
        flow_instance = ROUTE_MAP["general"]()


    state: AgentState = await flow_instance.run(state)        
    now = datetime.now().isoformat(timespec='seconds')
    if "quotation" in routes:
        response.messages.append(Message(
                sender=sender,
                message=state.quote_intermediate_results,
                timestamp=now
            ))
        save_client_state(request.userId,state=state)
        return response,state.rewritten_query
    
    response.messages.append(Message(
                sender=sender,
                message=state.final_answer,
                timestamp=now
            ))
    save_client_state(request.userId,state=state)
    add_short_term_memory_from_dict(user_id=float(state.customer_id), query=state.rewritten_query,response=state.final_answer)
    return response,state.rewritten_query