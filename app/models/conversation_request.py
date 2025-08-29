from pydantic import BaseModel
from typing import List
from datetime import datetime


class Message(BaseModel):
    sender: str
    message: str
    timestamp : datetime

class ConversationResponse(BaseModel):
    userId: str
    conversationId: str
    messages: List[Message]
    
class ConversationRequest(BaseModel):
    userId: str
    conversationId: str
    messages: Message

class StartConversation(BaseModel):
    userId : str

def conversation_helper(doc) -> dict:
    return {
        "userId": doc["userId"],
        "conversationId": doc["conversationId"],
        "messages": [
            {
                "sender": m["sender"],
                "message": m["message"],
                "timestamp": m["timestamp"].isoformat() if isinstance(m["timestamp"], datetime) else m["timestamp"]
            } for m in doc.get("messages", [])
        ]
    }