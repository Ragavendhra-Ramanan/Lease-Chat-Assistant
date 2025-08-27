from models.base_node import BaseNode
from langchain.chains import LLMChain
from utils.helper_functions import inject_filters
from models.base_llm import model
from langchain.prompts import PromptTemplate
from ..contract_search_prompt import CONTRACT_SEARCH_PROMPT
from db.weaviate_operations import async_query
from models.agent_state import AgentState
from utils.numeric_filters import extract_filters
from utils.contract_filter import parse_contract_string, filter_contract_data

class ContractNode(BaseNode):
    def __init__(self, client,df,limit):
        self.client = client
        self.contract_df = df
        self.limit = limit
    async def run(self, state:AgentState):

        results = {"contract": [], "vehicle": [], "product": []}
        vehicle_filters = extract_filters(state.vehicle_filters)
        product_filters = extract_filters(state.product_filters)
        #contract_filters = extract_filters(state.contract_filters)
        # --- Contract search ---
        if "contract" in state.route:
            # contract_query = inject_filters(state.rewritten_query, state.contract_filters, "contract")
            # contract_collection = self.client.collections.get("Contract")
            # contract_results = await async_query(contract_collection,
            #                      query=contract_query,
            #                      alpha=0.75, 
            #                      filters="customerID",
            #                      filter_val=customer_id,
            #                      where=contract_filters,
            #                      limit=0)
            print(state,"inner")
            parsed_contract_filter = parse_contract_string(state.contract_filters)
            contract_results = filter_contract_data(filter_dict=parsed_contract_filter,df=self.contract_df,customer_id=state.customer_id)
            results["contract"] = contract_results
            state.trace.append(["CONTRACT VECTOR", f"Retrieved {len(results['contract'])} docs"])
        # Vehicle IDs from contracts
        if "vehicle" in state.route and (state.vehicle_filters or vehicle_ids) and len(contract_results)>0:
            vehicle_ids = [c.get("Vehicle ID") for c in results["contract"] if c.get("Vehicle ID")]
            vehicle_query = inject_filters(state.rewritten_query, state.vehicle_filters, "vehicle")
            vehicle_collection = self.client.collections.get("Car")
            vehicle_results = await async_query(collection=vehicle_collection,
                                 query=vehicle_query,
                                 filters="vehicle_id",
                                 filter_val=vehicle_ids,
                                 where=vehicle_filters,
                                 alpha=0.6, 
                                 limit=self.limit)
            results["vehicle"] = vehicle_results
            state.trace.append(["CONTRACT VEHICLE VECTOR", f"Retrieved {len(results['vehicle'])} docs"])

        # Product IDs from contracts
        if "product" in state.route and (state.product_filters or product_ids) and len(contract_results)>0:
            product_ids = [c.get("Product ID") for c in results["contract"] if c.get("Product ID")]
            product_query = inject_filters(state.rewritten_query, state.product_filters, "product")
            product_collection = self.client.collections.get("Product")
            product_results = await async_query(collection=product_collection,
                                 query=product_query,
                                 alpha=0.6,
                                 filters="product_id",
                                 filter_val=product_ids ,
                                 where=product_filters,
                                 limit=self.limit) 
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
