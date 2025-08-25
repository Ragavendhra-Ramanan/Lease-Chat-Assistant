from models.base_node import BaseNode
from langchain.chains import LLMChain
from utils.helper_functions import inject_filters
from models.base_llm import model
from langchain.prompts import PromptTemplate
from ..vehicle_search_prompt import VEHICLE_SEARCH_PROMPT
from db.weaviate_operations import async_query
from models.agent_state import AgentState

class VehicleNode(BaseNode):
    def __init__(self, client):
        self.client = client
    async def run(self, state:AgentState):
        vehicle_query = inject_filters(state.rewritten_query, state.vehicle_filters, "vehicles")
        # search
        vehicle_collection = self.client.collections.get("Vehicle")
        context = await async_query(collection=vehicle_collection,
                                 query=vehicle_query,
                                 alpha=0.75, 
                                 limit=5)
        vehicle_summary = []  
        for obj in context:
            vehicle_summary.append(obj.get("summary"))  

        state.vehicle_vector_result = vehicle_summary
        state.trace.append(["VEHICLE VECTOR", f"Retrieved {len(vehicle_summary)} docs"])
        vehicle_prompt = PromptTemplate(
            template=VEHICLE_SEARCH_PROMPT,
            input_variables=["context","query"],
        )
        chain = LLMChain(llm=model, prompt=vehicle_prompt)
        result = await chain.ainvoke({"context": vehicle_summary, "query": vehicle_query})
        state.final_answer = result["text"]
        state.trace.append(["VEHICLE ANSWER", result["text"][:80] + ("..." if len(result["text"]) > 80 else "")])
        return state
