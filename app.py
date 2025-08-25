from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["chat_db"]
conversations_collection = db["conversations"]

# Pydantic models
class Message(BaseModel):
    role: Literal["user", "system"]
    content: str
    timestamp: datetime

class MessageCreate(BaseModel):
    user_id: str
    conversation_id: str
    messages: List[Message]

class ConversationRequest(BaseModel):
    user_id: str
    conversation_id: str

class Conversation(BaseModel):
    user_id: str
    conversation_id: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime

# Helper function to convert MongoDB document to Pydantic-friendly dict
def conversation_helper(doc) -> dict:
    return {
        "user_id": doc["user_id"],
        "conversation_id": doc["conversation_id"],
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "timestamp": m["timestamp"].isoformat() if isinstance(m["timestamp"], datetime) else m["timestamp"]
            } for m in doc.get("messages", [])
        ],
        "created_at": doc["created_at"].isoformat() if isinstance(doc["created_at"], datetime) else doc["created_at"], #doc["created_at"].strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        "updated_at": doc["updated_at"].isoformat() if isinstance(doc["updated_at"], datetime) else doc["updated_at"]
    }

app = FastAPI()

# GET: Retrieve full conversation by user_id and conversation_id
@app.get("/conversations/", response_model=Conversation)
async def get_conversation(req: ConversationRequest):
    try:
        user_id = req.user_id
        conversation_id = req.conversation_id
        convo = await conversations_collection.find_one({"user_id": req.user_id,"conversation_id": conversation_id})
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation_helper(convo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
# POST: Add a message to a conversation (create new conversation if needed)
@app.post("/conversations/", response_model=Conversation)
async def add_message(message: MessageCreate = ...):
    try:
        # Check if conversation exists
        conversation_id = message.conversation_id
        convo = await conversations_collection.find_one({"conversation_id": conversation_id})
                
        message_data = [msg.model_dump() for msg in message.messages]
        now = datetime.now().isoformat(timespec='seconds') #.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if convo:
            # Validate user_id matches
            if convo["user_id"] != message.user_id:
                raise HTTPException(status_code=400, detail="user_id does not match conversation owner")

            # Append message to existing conversation
            update_result = await conversations_collection.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {"messages": { "$each": message_data }},
                    "$set": {"updated_at": now}
                }
            )
        else:
            # Create new conversation document
            convo_doc = {
                "user_id": message.user_id,
                "conversation_id": conversation_id,
                "messages": message_data,
                "created_at": now,
                "updated_at": now,
            }
            await conversations_collection.insert_one(convo_doc)

        # Return updated conversation
        updated_convo = await conversations_collection.find_one({"conversation_id": conversation_id})
        if not updated_convo:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated conversation")

        return conversation_helper(updated_convo)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")