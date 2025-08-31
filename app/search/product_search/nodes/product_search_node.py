from models.base_node import BaseNode
from langchain.chains import LLMChain
from models.base_llm import model
from utils.helper_functions import inject_filters
from langchain.prompts import PromptTemplate
from ..product_search_prompt import PRODUCT_SEARCH_PROMPT
from db.weaviate_operations import async_query
from models.agent_state import AgentState
from utils.numeric_filters import extract_filters
from conversation_intents.extract_conversation_intent import append_preference,save_all_to_file
class ProductNode(BaseNode):
    def __init__(self,client, limit):
        self.client = client
        self.limit = limit

    async def run(self, state:AgentState):
        print(state.product_filters,"filter")
        append_preference(user_id=int(state.customer_id),preference_string=state.product_filters,types="product")
        save_all_to_file(types="product")
        product_query = inject_filters(state.rewritten_query, state.product_filters, "product")
        where_filters = extract_filters(state.product_filters)
        product_collection = self.client.collections.get("Product")
        context = await async_query(collection=product_collection,
                                 query=product_query,
                                 alpha=0.9, 
                                 where=where_filters,
                                 limit=self.limit)   
        product_summary = []  
        for obj in context:
            product_summary.append(obj.get("summary"))  

        state.product_vector_result = product_summary
        state.trace.append(["PRODUCT VECTOR", f"Retrieved {len(product_summary)} docs"])
        product_prompt = PromptTemplate(
            template=PRODUCT_SEARCH_PROMPT,
            input_variables=["context","query"],
        )
        chain = LLMChain(llm=model, prompt=product_prompt)
        result = await chain.ainvoke({"context": product_summary, "query": product_query})
        state.final_answer = result["text"]
        state.trace.append(["PRODUCT ANSWER", result["text"][:80] + ("..." if len(result["text"]) > 80 else "")])
        return state
