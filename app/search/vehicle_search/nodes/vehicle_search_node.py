from models.base_node import BaseNode
from langchain.chains import LLMChain
from utils.helper_functions import inject_filters
from models.base_llm import model
from langchain.prompts import PromptTemplate
from ..vehicle_search_prompt import VEHICLE_SEARCH_PROMPT
from db.weaviate_operations import async_query
from models.agent_state import AgentState
from utils.numeric_filters import extract_filters
from conversation_intents.extract_conversation_intent import append_preference, save_all_to_file
class VehicleNode(BaseNode):
    def __init__(self, client, limit):
        self.client = client
        self.limit = limit
    async def run(self, state:AgentState):

        append_preference(user_id=int(state.customer_id),preference_string=state.vehicle_filters,types="vehicle")
        save_all_to_file(types="vehicle")
        is_ev = state.is_ev  
        where_filters=extract_filters(state.vehicle_filters)
        vehicle_query = inject_filters(state.rewritten_query, state.vehicle_filters, "vehicles")
        # search
        vehicle_collection = self.client.collections.get("Car")
        context = await self._call_llm(state=state,
            collection=vehicle_collection,
                                 query=vehicle_query,
                                 filter= where_filters,
                                 alpha=0.75, 
                                 limit=self.limit)
        if not is_ev:
            ev_context = await self._call_llm(state=state,
                collection=vehicle_collection,
                                 query=vehicle_query+"with EV",
                                 filter= where_filters,
                                 alpha=0.75, 
                                 limit=2)
            context.extend(ev_context)
        vehicle_summary_str = "\n\n".join(f"{i+1}. {ctx}" for i, ctx in enumerate(context))
        vehicle_prompt = PromptTemplate(
            template=VEHICLE_SEARCH_PROMPT,
            input_variables=["context","query"],
        )
        chain = LLMChain(llm=model, prompt=vehicle_prompt)
        result = await chain.ainvoke({"context": vehicle_summary_str, "query": vehicle_query})
        state.trace.append(["VEHICLE ANSWER", result["text"][:80] + ("..." if len(result["text"]) > 80 else "")])
        state.final_answer = result["text"]
        return state
    async def _call_llm(self,state,collection, query, alpha, limit,filter):
        context = await async_query(collection=collection,
                                 query=query,
                                 alpha=alpha, 
                                 where=filter,
                                 limit=limit)
        vehicle_summary = []  
        for obj in context:
            vehicle_summary.append(obj.get("summary"))  
        state.vehicle_vector_result = vehicle_summary
        state.trace.append(["VEHICLE VECTOR", f"Retrieved {len(vehicle_summary)} docs"])
        return vehicle_summary
