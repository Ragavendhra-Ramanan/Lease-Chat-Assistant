# Step 1: Define output schema
from pydantic import BaseModel, Field
from typing import Optional, ClassVar, Dict, List
from langchain.schema import BaseMemory

#router parser
# class ClarifierOutput(BaseModel):
#     action: str = Field(..., description="Next Action for the given query")
#     clarifying_question : Optional[str]= Field(description="domain-specific clarifying question")
class ClarifierOutput(BaseModel):
    rewritten_query: str
    contract_filters: Dict[str, str]
    vehicle_filters: Dict[str, str]
    product_filters: Dict[str, str]
    quote_filters: Dict[str, str]
    action: str  # router | decomposition | clarify
    clarifying_question: Optional[str]
    route: List[str]  # ["contract","vehicle","product","quote"]
    is_ev: str  # "yes" | "no"
    retrieval_mode: str  # "MMR" | "SIMILARITY"
