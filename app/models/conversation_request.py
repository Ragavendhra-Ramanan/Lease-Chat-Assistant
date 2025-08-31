from pydantic import BaseModel
from typing import List
from datetime import datetime


class Message(BaseModel):
    sender: str
    message: str
    timestamp : datetime
    fileStream: str

class ConversationResponse(BaseModel):
    messages: List[Message]
    userId: float
    conversationId: str

class ConversationRequest(BaseModel):
    messages: Message
    userId: float
    conversationId: str

class StartConversation(BaseModel):
    userId : str
def conversation_helper(doc) -> dict:
    return {
        "userId": doc.get("userId"),
        "conversationId": doc.get("conversationId"),
        "messages": [
            {
                "sender": m.get("sender"),
                "message": m.get("message"),
                "timestamp": m.get("timestamp").isoformat(timespec='seconds') if isinstance(m.get("timestamp"), datetime) else m.get("timestamp"),
                "fileStream": m.get("fileStream")
            } for m in doc.get("messages", [])
        ]
    }