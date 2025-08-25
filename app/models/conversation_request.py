from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    role: str
    message: str

class ConversationRequest(BaseModel):
    messages: List[Message]
    userid: float
    conversation_id: str