from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from db.vectordb_operations import connection_to_wcs, close_connection
from utils.secrets import weaviate_api_key, weaviate_url, openai_api_key
from models.conversation_request import ConversationRequest
from router.nodes.router_node import RouteNode
from models.agent_state import AgentState
from uuid import uuid4
from typing import Dict
from utils.flows import ROUTE_MAP
import copy
client = None
router = RouteNode()


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

@app.post("/conversation/start")
async def start_conversation(request:ConversationRequest,
                       state: AgentState = Depends(get_state)):
    """Start a new conversation and return conversation_id."""
    conversation_id = str(uuid4())
    state["customer_id"] = request.userid
    welcome = {"role": "assistant", "message": "Hi, welcome!"}
    request.conversation_id = conversation_id
    request.messages = welcome 
    return request



@app.post("/conversation/messages")
async def get_conversation_result(request: ConversationRequest,
                                  state: AgentState = Depends(get_state)):
    
    query = request.messages[-1].message
    state.query = query
    state = await router.run(state)
    routes = state.route
    flow_instance = None
    state.customer_id = request.userid
    # Pick flow by checking membership
    if "quotation" in routes:
        flow_instance = ROUTE_MAP["quotation"]()
    elif "contract" in routes:
        flow_instance = ROUTE_MAP["contract"](client=client)
    elif "product" in routes:
        flow_instance = ROUTE_MAP["product"](client=client)
    elif "vehicle" in routes:
        flow_instance = ROUTE_MAP["vehicle"](client=client)
    else:
        flow_instance = ROUTE_MAP["general"]()

    response: AgentState = await flow_instance.run(state)
    return response.final_answer
    


