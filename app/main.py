from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from db.vectordb_operations import connection_to_wcs, close_connection
from utils.secrets import weaviate_api_key, weaviate_url, openai_api_key, mongo_uri
from models.conversation_request import ConversationResponse, ConversationRequest, Message, StartConversation, conversation_helper
from router.nodes.router_node import RouteNode
from models.agent_state import AgentState
from clarifier_agent.nodes.clarifier_node import ClarifierNode
from uuid import uuid4
import json
import os
from collections import Counter
from datetime import datetime
from typing import Dict, List
from utils.flows import ROUTE_MAP
from utils.helper_functions import get_data, filter_df
from models.auth_models import User, SignupResponse, Login, LoginResponse, GuestLogin, GuestLoginResponse
from fastapi.middleware.cors import CORSMiddleware
from memory.memory_store import get_recent_memory, add_short_term_memory_from_dict
from decomposition.nodes.decomposition_node import DecompositionNode
from decomposition.nodes.decomposition_result_node import DecompositionResultNode
from utils.helper_functions import USER_CSV_FILE, load_user_data,GUEST_USER_CSV_FILE
from  search.other_search.nodes.other_search_node import GeneralSearchNode
from recommendation.recommender_engine import (
     get_new_user_recommendation, get_potential_customer_recommendation,get_potential_user_engagement_recommendation,
     get_customer_retention_recommendation)
import pandas as pd 
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import random
import base64
from io import BytesIO
#from fpdf import FPDF

origins = [
    "http://localhost:4200",  # frontend URL
    "http://127.0.0.1:4200",  # optional
]

global country
client = None
router = RouteNode()
decomposition = DecompositionNode()
decomposition_result = DecompositionResultNode()
clarifier_node = ClarifierNode()
general_node = GeneralSearchNode()
vehicle_df, product_df,contract_df, guest_user_df = get_data()
quote_filtering_node = ROUTE_MAP["filtering"](vehicle_df, product_df, filter_df)
quote_update_node = ROUTE_MAP["quote_field_update"]()
quote_generate_node = ROUTE_MAP["quote"]()

message_buffer: List[ConversationResponse] = []
MAX_BATCH_SIZE = 20
buffer_lock = asyncio.Lock()
# Initialize in main.py
conversations: Dict[str, Dict[str, any]] = {}
def get_client_state(user_id: str,conversation_id:str) -> AgentState:
    if user_id not in conversations:
        conversations[user_id] = dict()
    if conversation_id not in conversations[user_id]:
        conversations[user_id][conversation_id]=AgentState()
    return conversations[user_id][conversation_id]

def save_client_state(user_id: str, conversation_id:str, state: AgentState):
    conversations[user_id][conversation_id] = state

def get_last_query(user_id: str,conversation_id:str) -> str:
    """
    Returns the last user query from memory, or empty string if none.
    """
    recent_memory = get_recent_memory(user_id,conversation_id)
    if not recent_memory:
        return ""
    return recent_memory[-1]["query"]   

def user_exists_in_search(user_id) -> bool:
    """Check if a user_id exists in the JSON data"""
    # Load JSON file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir,"data/conversation_intents/vehicles/unstructured_vehicle.json"), "r") as f:
        data = json.load(f)
        print(data,"data")
    return str(int(user_id)) in data

def get_quote_data() -> bool:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    quote_df = pd.read_csv(os.path.join(base_dir,"data/quote_data_new.csv"))
    return quote_df

def get_country(userId):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    user_df = pd.read_csv(os.path.join(base_dir,"data/user_data.csv"))
    matched= user_df[user_df['userId']==userId]
    if matched.empty:
        return None
    return matched.iloc[0]['country']




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
                userId= str(user_data['userId']),
                userName= str(user_data['firstName']) + " "+ str(user_data['lastName']) 
            )

    return login_response

@app.post("/api/auth/guestLogin")
async def guest_user(credentials : GuestLogin):
    df = pd.read_csv(GUEST_USER_CSV_FILE)
    contact = credentials.contact
    
    # Check user by email or mobile
    user_row = df[(df["contact"] == contact)]   
    if user_row.empty:
        guser_id = str(random.randint(5000,9999))
        guest_user = {
        "userId": guser_id,
        "contact": contact
        }    
        df = pd.concat([df, pd.DataFrame([guest_user])], ignore_index=True)
        df.to_csv(GUEST_USER_CSV_FILE, index=False)
    else:
        user_data = user_row.iloc[0].to_dict()  
        guser_id =  user_data["userId"] 
        
    guest_login_response = GuestLoginResponse(
                userId=str(guser_id),
    )
    return guest_login_response

@app.get("/api/chat/getConversations/{userId}", response_model=List[ConversationResponse])
async def get_conversation(userId: str):
    convo = await conversations_collection.find({"userId": userId}).to_list()
    if not convo:
        return []
    return [conversation_helper(c) for c in convo]

@app.post("/api/chat/startNewConversation")
async def start_conversation(request:StartConversation):
    """Start a new conversation and return conversation_id."""
    await flush_buffer_to_db()
    conversation_id = str(uuid4())
    now = datetime.now().isoformat(timespec='seconds')
    welcome = Message(
        sender="bot",
        message="""
        Hi! Welcome to our Leasing Assistant

        I can help you with:

        1. Product Search - Find the right products for your needs.
        2. Vehicle Search - Browse and compare vehicles.
        3. Contract Search - Access and review your contracts.
        4. Quote Generation - Get personalized lease quotes.
        """,
         timestamp=now,
        fileStream=""
    )
    response = ConversationResponse(
        userId= request.userId,
        conversationId=conversation_id,
        messages=[welcome]
    )
    convo_doc = {
        "userId": request.userId,
        "conversationId": conversation_id,
        "messages": welcome.model_dump()
    }
    message_buffer.append(convo_doc)
    return response

@app.get("/api/chat/recommendations/{userID}")
async def recommendations(userID:int):
    quote_df = await asyncio.to_thread(get_quote_data)
    country = await asyncio.to_thread(get_country,userID)
    if(userID in contract_df['Customer ID'].values):
        return await get_customer_retention_recommendation(client=client,user_id=userID)
    elif (userID in quote_df['User ID'].values):
        return await get_potential_customer_recommendation(user_id=userID,client=client)
    elif await asyncio.to_thread(user_exists_in_search,userID):
        return await get_potential_user_engagement_recommendation(client=client, user_id=userID,country=country)
    else:
        return await get_new_user_recommendation(country=country)
    #print(await get_user_preferences(client=client,user_id=userID))
    #return 

@app.post("/api/chat/sendMessage")
async def send_bot_message(request: ConversationRequest):
    conversationId = request.conversationId
    userId = request.userId      
            
    message_data = request.messages.model_dump()
    convo_doc = {
            "userId": userId,
            "conversationId": conversationId,
            "messages": message_data
    }
    
    message_buffer.append(convo_doc)
    if len(message_buffer) >= MAX_BATCH_SIZE:
        # Flush the buffer to MongoDB
        await flush_buffer_to_db()
    final_message:str =""
    state = get_client_state(request.userId,request.conversationId)
    state.previous_query = get_last_query(request.userId,request.conversationId)
    state.query = request.messages.message
    state.customer_id =  request.userId
    state.country = await asyncio.to_thread(get_country,userId)
    response = ConversationResponse(
            messages=[request.messages],              # empty list or actual messages
            userId= request.userId  ,     # string
            conversationId=request.conversationId # string
            )
    if "quotation" in state.route:
        final_message= await run_quotation_node(request=request)
        now = datetime.now().isoformat(timespec='seconds')  
        response.messages.append(Message(
            sender="bot",
            message=final_message,
            timestamp=now,
            fileStream=""
        ))
        convo_doc = {
        "userId": request.userId,
        "conversationId": request.conversationId,
        "messages": response.messages[-1].model_dump()
        }
        message_buffer.append(convo_doc)
        return response
    state = await router.run(state)
    save_client_state(user_id=request.userId,conversation_id=request.conversationId,state=state)
    if len(state.route) ==0:
        general_state=await general_node.run(state)
        final_message = general_state.final_answer
    elif state.action =="clarify":
        final_message=state.clarifying_question
    elif state.action =="decomposition":
        response = await decompose_tasks(request=request)
        convo_doc = {
        "userId": request.userId,
        "conversationId": request.conversationId,
        "messages": response.messages[-1].model_dump()
        }
        message_buffer.append(convo_doc)
        return response
    elif "quotation" in state.route:
        state.quote_context = "vehicle"
        save_client_state(user_id=request.userId,conversation_id=request.conversationId,state=state)
        state:AgentState = await quote_filtering_node.run(state)
        save_client_state(user_id=request.userId,conversation_id=request.conversationId,state=state)
        final_message = state.quote_intermediate_results
    else:
        response,rewritten_query = await get_conversation_result(request=request,router_passed=True)
        convo_doc = {
        "userId": request.userId,
        "conversationId": request.conversationId,
        "messages": response.messages[-1].model_dump()
        }
        message_buffer.append(convo_doc)
        return response
    now = datetime.now().isoformat(timespec='seconds')  
    response.messages.append(Message(
            sender="bot",
            message=final_message,
            timestamp=now,
            fileStream=""
        ))
    add_short_term_memory_from_dict(
        user_id=request.userId,
        conversation_id=request.conversationId,
        query=state.query,
        response=state.final_answer
    )
    convo_doc = {
    "userId": request.userId,
    "conversationId": request.conversationId,
    "messages": response.messages[-1].model_dump()
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
                        "userId": str(int(msg.get("userId"))),
                        "conversationId": msg.get("conversationId")
                    },
                    {
                        "$push": {"messages": msg.get("messages")}
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

async def decompose_tasks(request: ConversationRequest):
    context=[]
    questions = []
    query = request.messages.message
    state = get_client_state(request.userId,request.conversationId)
    decomposition_values, rewritten_query = await decomposition.run(query)
    print("\nTasks To do\n")
    print(decomposition_values)
    for task, retriever in decomposition_values:
        if retriever: 
            request.messages.message = task
            task_response , query_retrieved = await get_conversation_result(request=request,router_passed=False)
            print("\nResponse\n")
            print(state.final_answer)
            questions.append(query_retrieved)
            context.append([f"{task} : {state.final_answer}"])
        else:
            questions.append(task)

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
        timestamp=now,
        fileStream=""
    ))
    add_short_term_memory_from_dict(user_id=request.userId,conversation_id=request.conversationId,query=",".join(questions),response=response)
    return response

async def run_quotation_node(request:ConversationRequest):
    state = get_client_state(request.userId,request.conversationId)
    state:AgentState = await quote_update_node.run(state)
    if state.quote_next_agent == "filtering":
        state = await quote_filtering_node.run(state)
        save_client_state(request.userId,request.conversationId,state=state)
        return state.quote_intermediate_results
    
    elif state.quote_next_agent == "quote":
        quote_df = await asyncio.to_thread(get_quote_data)
        state = await quote_generate_node.run(state,contract_df,quote_df)
        state.route = ""
        state.quote_step = "preowned"
        state.quote_context = ""
        state.quote_next_agent = ""
        save_client_state(request.userId,conversation_id=request.conversationId,state=state)
        return state.quote_results

async def get_conversation_result(request: ConversationRequest,router_passed:bool):    
    query = request.messages.message
    state = get_client_state(request.userId,request.conversationId)
    state.trace = [[]]
    state.previous_query = get_last_query(state.customer_id,conversation_id=request.conversationId)
    state.query = query
    response = ConversationResponse(
    messages=[request.messages],              # empty list or actual messages
    userId= request.userId  ,     # string
    conversationId=request.conversationId # string
    )
    sender = "bot"
    response.conversationId = request.conversationId
    response.userId = request.userId
    if not router_passed:
        state = await router.run(state)
    flow_instance = None
    state.customer_id = request.userId
    print("\nCurrent task\n")
    print(state.rewritten_query)
    print(state.route,"route")    
    limit = 5
    # Pick flow by checking membership
    if "contract" in state.route:
        flow_instance = ROUTE_MAP["contract"](client=client,df=contract_df,limit=limit)
    elif "product" in state.route:
        flow_instance = ROUTE_MAP["product"](client=client,limit=limit,guest_user_df=guest_user_df)
    elif "vehicle" in state.route:
        flow_instance = ROUTE_MAP["vehicle"](client=client,limit=limit,guest_user_df=guest_user_df)
    else:
        flow_instance = ROUTE_MAP["general"]()
    state: AgentState = await flow_instance.run(state)
    now = datetime.now().isoformat(timespec='seconds')  
    response.messages.append(Message(
                sender=sender,
                message=state.final_answer,
                timestamp=now,
                fileStream=""
            ))
    save_client_state(request.userId,request.conversationId,state=state)
    add_short_term_memory_from_dict(user_id=state.customer_id, conversation_id=request.conversationId,query=state.rewritten_query,response=state.final_answer)
    return response, state.rewritten_query

