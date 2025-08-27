from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from db.vectordb_operations import connection_to_wcs, close_connection
from utils.secrets import weaviate_api_key, weaviate_url, openai_api_key
from models.conversation_request import ConversationResponse, ConversationRequest, Message, StartConversation
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
    # startup
    client = connection_to_wcs(weaviate_url=weaviate_url,
                               weaviate_api_key=weaviate_api_key,
                               openai_api_key=openai_api_key)
    yield
    # shutdown
    close_connection(client=client)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # allow specific origins
    allow_credentials=True,
    allow_methods=["*"],             # allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

@app.post("/api/auth/signup")
async def signup_user(user_info:User):
    signup_response = SignupResponse(
        value=True
    )
    return signup_response


@app.post("/api/auth/login")
async def login_user(login_info : Login):
    login_response = LoginResponse(
        userId="1016"
    )
    return login_response

@app.post("/api/chat/startNewConversation")
async def start_conversation(request:StartConversation):
    """Start a new conversation and return conversation_id."""
    state = get_client_state(request.userId)
    conversation_id = str(uuid4())
    welcome = Message(
        sender="bot",
        message="Hi, welcome! I will help in product search, vehicle search, contract search and quote generation"
    )
    response = ConversationResponse(
        userId= request.userId,
        conversationId=conversation_id,
        messages=[welcome]
    )
    state.customer_id = request.userId
    save_client_state(request.userId, state)
    return response

@app.get("/api/chat/recommendations/{userID}")
async def recommendations(userID:int):
    return ["New EV toyoto cars", "Flexi lease term 24 months" , "Ford lesser than $40000"]

@app.post("/api/chat/sendMessage")
async def decompose_tasks(request: ConversationRequest):
    context=[]
    questions = []
    query = request.messages.message
    state = get_client_state(request.userId)
    if "quotation" not in state.route:
        decomposition_values, rewritten_query = await decomposition.run(query)
        flag = False
        for task, retriever in decomposition_values:
            if retriever: 
                flag = True
                request.messages.message = task
                task_response , query_retrieved = await get_conversation_result(request=request)
                questions.append(query_retrieved)
                context.append([f"{task} : {state.final_answer}"])
        if flag:
            if len(questions) == 0:
                questions.append(rewritten_query)  
            final_answer = await decomposition_result.run(context=context,questions=questions)
            response = ConversationResponse(
                messages=[request.messages],              # empty list or actual messages
                userId= request.userId  ,     # string
                conversationId=request.conversationId # string
                )
            response.messages.append(Message(
                sender="bot",
                message=final_answer
            ))
        else:
            response,query_retrieved= await get_conversation_result(request=request)
            questions.append(query_retrieved)
        add_short_term_memory_from_dict(user_id=request.userId,query=",".join(questions),response=response)

    else:
        response = await get_conversation_result(request=request)
    return response
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
            response.messages.append(Message(
                sender=sender,
                message=state.quote_intermediate_results

            ))
            return response,state.rewritten_query
        elif state.quote_next_agent == "quote":
            state = await quote_generate_node.run(state)
            state.route = ""
            state.quote_step = "preowned"
            state.quote_context = ""
            state.quote_next_agent = ""
            save_client_state(request.userId,state=state)
            response.messages.append(Message(
                sender=sender,
                message=state.quote_results
            )) 
            return response,state.rewritten_query

    state = await router.run(state)
    routes = state.route
    flow_instance = None
    state.customer_id = request.userId

        
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
    if "quotation" in routes:
        response.messages.append(Message(
                sender=sender,
                message=state.quote_intermediate_results
            ))
        save_client_state(request.userId,state=state)
        return response,state.rewritten_query
    response.messages.append(Message(
                sender=sender,
                message=state.final_answer
            ))
    save_client_state(request.userId,state=state)
    add_short_term_memory_from_dict(user_id=state.customer_id, query=state.rewritten_query,response=state.final_answer)
    return response,state.rewritten_query
