from models.base_node import BaseNode
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from ..clarifier_prompt import CLARIFIER_PROMPT
from models.base_llm import model
from models.clarifier_output import ClarifierOutput
from models.agent_state import AgentState
class ClarifierNode(BaseNode):
    async def run(self, state: AgentState):
        parser = PydanticOutputParser(pydantic_object=ClarifierOutput)
        clarifier_prompt = PromptTemplate(
            template=CLARIFIER_PROMPT,
            input_variables=["user_query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        clarifier_chain = LLMChain(
            llm=model,  # replace with async-compatible LLM
            prompt=clarifier_prompt,
            output_parser=parser
        )
        print(state)
        # Use asyncio to run sync invoke in thread if LLM is sync
        response = await clarifier_chain.ainvoke({"user_query": state.query})

        print(response['text'],"text")
        return state
