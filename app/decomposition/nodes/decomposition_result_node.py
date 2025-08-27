from models.base_node import BaseNode
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from ..decomposition_result_prompt import DECOMPOSITION_RESULT_PROMPT
from models.base_llm import model
class DecompositionResultNode(BaseNode):
    async def run(self, context,questions):
        router_prompt = PromptTemplate(
            template=DECOMPOSITION_RESULT_PROMPT,
            input_variables=["context_blocks","question_list"],
        )

        router_chain = LLMChain(
            llm=model,  # replace with async-compatible LLM
            prompt=router_prompt,
        )

        # Use asyncio to run sync invoke in thread if LLM is sync
        response = await router_chain.ainvoke({"context_blocks": context, "question_list":questions,
                                               })
        # state.rewritten_query = response['text'].rewritten_query
        # state.product_filters = response['text'].product_filters
        # state.vehicle_filters = response['text'].vehicle_filters
        # state.contract_filters = response['text'].contract_filters
        # state.is_ev = response['text'].is_ev
        # state.retrieval_mode = response['text'].retrieval_mode
        # state.trace.append(["ROUTER", f"Query='{state.query}' → Route='{decision}'"])
        return response['text']
