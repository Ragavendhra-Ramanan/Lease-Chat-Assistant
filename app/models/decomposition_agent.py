from pydantic import BaseModel, Field
from typing import List
# 1️⃣ Define Pydantic models
class TaskStep(BaseModel):
    step: int = Field(..., description="Step number")
    task: str = Field(..., description="Task description")
    retriever: bool = Field(..., description="True if task fetches data")

class TaskWorkflow(BaseModel):
    rewritten_query: str = Field(..., description="Clear, explicit version of the user query")
    steps: List[TaskStep] = Field(..., description="List of atomic executable steps")
