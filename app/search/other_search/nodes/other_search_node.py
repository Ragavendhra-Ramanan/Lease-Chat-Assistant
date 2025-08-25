from models.base_node import BaseNode
from langchain.chains import LLMChain
from models.base_llm import model
from langchain.prompts import PromptTemplate
from ..other_search_prompt import OTHER_SEARCH_PROMPT
from models.agent_state import AgentState
class GeneralSearchNode(BaseNode):
    async def run(self, state: AgentState):
        query = state.rewritten_query
        general_prompt = PromptTemplate(
            template=OTHER_SEARCH_PROMPT,
            input_variables=["context","query"],
        )

        chain = LLMChain(llm=model, prompt=general_prompt)

        # Async call instead of invoke
        result = await chain.ainvoke({"query": query})
        response = result["text"]

        state.trace.append([
            "GENERAL ANSWER",
            response[:80] + ("..." if len(response) > 80 else "")
        ])
        state.final_answer = response
        return state
