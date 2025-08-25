from models.base_node import BaseNode
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from ..router_prompt import ROUTER_PROMPT
from models.base_llm import model
from models.router_output import RouterOutput
from models.agent_state import AgentState

class RouteNode(BaseNode):
    async def run(self, state: AgentState):
        parser = PydanticOutputParser(pydantic_object=RouterOutput)
        router_prompt = PromptTemplate(
            template=ROUTER_PROMPT,
            input_variables=["input"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        router_chain = LLMChain(
            llm=model,  # replace with async-compatible LLM
            prompt=router_prompt,
            output_parser=parser
        )

        # Use asyncio to run sync invoke in thread if LLM is sync
        response = await router_chain.ainvoke({"input": state.query})

        decision = response["text"].route
        state.route = decision
        state.rewritten_query = response['text'].rewritten_query
        state.product_filters = response['text'].product_filters
        state.vehicle_filters = response['text'].vehicle_filters
        state.contract_filters = response['text'].contract_filters
        state.trace.append(["ROUTER", f"Query='{state.query}' → Route='{decision}'"])
        return state
