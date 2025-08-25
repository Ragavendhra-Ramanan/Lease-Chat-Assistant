from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from db.vectordb_operations import connection_to_wcs, close_connection
from utils.secrets import weaviate_api_key, weaviate_url, openai_api_key
from models.conversation_request import ConversationResponse, ConversationRequest, Message
from router.nodes.router_node import RouteNode
from models.agent_state import AgentState
from uuid import uuid4
from typing import Dict
from utils.flows import ROUTE_MAP
from utils.helper_functions import get_data, filter_df
from models.auth_models import User, SignupResponse, Login, LoginResponse
import copy

client = None
router = RouteNode()
vehicle_df, product_df = get_data()
quote_filtering_node = ROUTE_MAP["filtering"](vehicle_df, product_df, filter_df)
quote_update_node = ROUTE_MAP["quote_field_update"]()
quote_generate_node = ROUTE_MAP["quote"]()
quote_orchestrator = ROUTE_MAP["quotation"]()


# Initialize in main.py
DEFAULT_STATE: AgentState = AgentState()
conversations: Dict[str, AgentState] = {}
def get_state():
    return copy.deepcopy(DEFAULT_STATE)

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

@app.post("/api/auth/signup")
async def signup_user(user_info:User):
    signup_response = SignupResponse(
        value=True
    )
    return signup_response


@app.post("/api/auth/login")
async def login_user(login_info : Login):
    login_response = LoginResponse(
        userId="1807"
    )
    return login_response

@app.post("/api/chat/startNewConversation")
async def start_conversation(request:ConversationResponse,
                       state: AgentState = Depends(get_state)):
    """Start a new conversation and return conversation_id."""
    conversation_id = str(uuid4())
    state.customer_id = request.userId
    welcome = {"sender": "bot", "message": "Hi, welcome! I will help in product search, vehicle search, contract search and quote generation"}
    request.conversationId = conversation_id
    request.messages = welcome 
    return request


@app.post("/api/chat/sendMessage")
async def get_conversation_result(request: ConversationRequest,
                                  state: AgentState = Depends(get_state)):
    
    query = request.messages.message
    state.query = query
    response = ConversationResponse(
    messages=[request.messages],              # empty list or actual messages
    userId= request.userId  ,     # string
    conversationId=request.conversationId # string
    )
    sender = "bot"
    response.conversationId = request.conversationId
    response.userId = request.userId
    if "quotation" in state.route:
        state = await quote_orchestrator.run(state)
        if state.quote_next_agent == "filtering":
            state = await quote_filtering_node.run(state)
            state = await quote_update_node.run(state)
            state = await quote_orchestrator.run(state)
            response.messages.append(Message(
                sender=sender,
                message=state.quote_intermediate_results

            ))
            return response
        
        elif state.quote_next_agent == "quote":
            state = await quote_generate_node.run(state)
            state.route = ""
            state.quote_step = "preowned"
            state.quote_context = ""
            state.quote_next_agent = ""
            response.messages.append(Message(
                sender=sender,
                message=state.quote_results
            )) 
            return response

    state = await router.run(state)
    routes = state.route
    flow_instance = None
    state.customer_id = request.userId
    # Pick flow by checking membership
    if "quotation" in routes:
        flow_instance = ROUTE_MAP["quotation"]()
        state.quote_context = "vehicle"

    elif "contract" in routes:
        flow_instance = ROUTE_MAP["contract"](client=client)
    elif "product" in routes:
        flow_instance = ROUTE_MAP["product"](client=client)
    elif "vehicle" in routes:
        flow_instance = ROUTE_MAP["vehicle"](client=client)
    else:
        flow_instance = ROUTE_MAP["general"]()

    state = await flow_instance.run(state)
    if "quotation" in routes:
        state = await quote_filtering_node.run(state)
        response.messages.append(Message(
                sender=sender,
                message=state.quote_intermediate_results

            ))
        return response
    response.messages.append(Message(
                sender=sender,
                message=state.final_answer
            ))
    return response
    


