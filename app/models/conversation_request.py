from pydantic import BaseModel
from typing import List
from datetime import datetime


class Message(BaseModel):
    sender: str
    message: str

class ConversationResponse(BaseModel):
    messages: List[Message]
    userId: float
    conversationId: str

class ConversationRequest(BaseModel):
    messages: Message
    userId: float
    conversationId: str
    timestamp : datetime

class StartConversation(BaseModel):
    userId : str