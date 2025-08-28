from models.base_node import BaseNode
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from ..decomposition_prompt import DECOMPOSITION_PROMPT
from models.base_llm import model
from models.decomposition_agent import TaskWorkflow
from models.agent_state import AgentState
class DecompositionNode(BaseNode):
    async def run(self, query):
        parser = PydanticOutputParser(pydantic_object=TaskWorkflow)
        router_prompt = PromptTemplate(
            template=DECOMPOSITION_PROMPT,
            input_variables=["user_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        router_chain = LLMChain(
            llm=model,  # replace with async-compatible LLM
            prompt=router_prompt,
            output_parser=parser
        )

        # Use asyncio to run sync invoke in thread if LLM is sync
        response = await router_chain.ainvoke({"user_query": query
                                               })
        results = [(value.task,value.retriever) for value in response['text'].steps]
        rewritten_query = response['text'].rewritten_query
        # state.rewritten_query = response['text'].rewritten_query
        # state.product_filters = response['text'].product_filters
        # state.vehicle_filters = response['text'].vehicle_filters
        # state.contract_filters = response['text'].contract_filters
        # state.is_ev = response['text'].is_ev
        # state.retrieval_mode = response['text'].retrieval_mode
        # state.trace.append(["ROUTER", f"Query='{state.query}' → Route='{decision}'"])
        return results, rewritten_query
