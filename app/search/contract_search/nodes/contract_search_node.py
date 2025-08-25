from models.base_node import BaseNode
from langchain.chains import LLMChain
from utils.helper_functions import inject_filters
from models.base_llm import model
from langchain.prompts import PromptTemplate
from ..contract_search_prompt import CONTRACT_SEARCH_PROMPT
from db.weaviate_operations import async_query
from models.agent_state import AgentState

class ContractNode(BaseNode):
    def __init__(self, client):
        self.client = client
    async def run(self, state:AgentState):
        customer_id = state.customer_id
        results = {"contract": [], "vehicle": [], "product": []}

        # --- Contract search ---
        if "contract" in state.route:
            contract_query = inject_filters(state.rewritten_query, state.contract_filters, "contract")
            contract_collection = self.client.collections.get("Contract")
            contract_results = await async_query(contract_collection,
                                 query=contract_query,
                                 alpha=0.75, 
                                 filters="customerID",
                                 filter_val=customer_id,
                                 limit=5)
            results["contract"] = contract_results
            print(len(results["contract"]))
            state.trace.append(["CONTRACT VECTOR", f"Retrieved {len(results['contract'])} docs"])

        # Vehicle IDs from contracts
        vehicle_ids = [c.get("vehicleID") for c in results["contract"] if c.get("vehicleID")]
        if "vehicle" in state.route and (state.vehicle_filters or vehicle_ids):
            vehicle_query = inject_filters(state.rewritten_query, state.vehicle_filters, "vehicle")
            vehicle_collection = self.client.collections.get("Vehicle")
            vehicle_results = await async_query(collection=vehicle_collection,
                                 query=vehicle_query,
                                 filters="vehicleID",
                                 filter_val=vehicle_ids,
                                 alpha=0.75, 
                                 limit=5)
            results["vehicle"] = vehicle_results
            state.trace.append(["CONTRACT VEHICLE VECTOR", f"Retrieved {len(results['vehicle'])} docs"])

        # Product IDs from contracts
        product_ids = [c.get("product_id") for c in results["contract"] if c.get("product_id")]
        if "product" in state.route and (state.product_filters or product_ids):
            product_query = inject_filters(state.rewritten_query, state.product_filters, "product")
            product_collection = self.client.collections.get("Product")
            product_results = await async_query(collection=product_collection,
                                 query=product_query,
                                 alpha=0.75,
                                 filters="productID",
                                 filter_val=product_ids ,
                                 limit=5) 
            results["product"] = product_results
            state.trace.append(["CONTRACT PRODUCT VECTOR", f"Retrieved {len(results['product'])} docs"])

        # LLM final answer
        contract_prompt = PromptTemplate(
            template=CONTRACT_SEARCH_PROMPT,
            input_variables=["context","query"],
        )
        chain = LLMChain(llm=model, prompt=contract_prompt)
        result = await chain.ainvoke({"context": results, "query": state.rewritten_query})
        state.final_answer = result["text"]
        state.trace.append(["CONTRACT ANSWER", result["text"][:80] + ("..." if len(result["text"]) > 80 else "")])
        return state
