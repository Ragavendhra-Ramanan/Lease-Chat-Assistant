# Step 1: Define output schema
from pydantic import BaseModel, Field
from typing import List

#router parser
class RouterOutput(BaseModel):
    rewritten_query: str = Field(..., description="Rewritten, clarified query")
    contract_filters: str = Field(description="The contract related filter")
    vehicle_filters: str= Field(description="The vehicle related filter")
    product_filters: str = Field(description="The product related filter")
    route: List[str] = Field(description="The chosen route: vehicle, product, contract, general, quotation")
    is_ev: str = Field(description="Flag to indicate whether the query is related to electric vehicle or not")
    retrieval_mode: str = Field(description="Retrieval method : MMR | SIMILARITY") 