from langchain_openai import ChatOpenAI
from utils.secrets import openai_api_key

#Define LLM
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0.4,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=openai_api_key
)