from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class AgentState:
    query: str = ""
    previous_query: str = ""
    retrieval_mode: str = ""
    route: List[str] = field(default_factory=list)
    product_vector_result: str = ""
    vehicle_vector_result: str = ""
    contract_vector_result: str = ""
    rewritten_query: str = ""
    contract_filters: str = ""
    vehicle_filters: str = ""
    product_filters: str = ""
    final_answer: str = ""
    trace: List[List[str]] = field(default_factory=list)
    customer_id: float = 0
    quote_step: str = "preowned"  # initial step
    quote_filters: Dict[str, Any] = field(default_factory=dict)
    quote_vehicle_candidates: List[Dict[str, Any]] = field(default_factory=list)
    quote_product_candidates: List[Dict[str, Any]] = field(default_factory=list)
    quote_final_vehicle: Optional[Dict[str, Any]] = None
    quote_final_product: Optional[Dict[str, Any]] = None
    quote: Optional[Dict[str, Any]] = None
    quote_intermediate_results: str = ""
    quote_next_agent: str = ""
    quote_context: str = ""
    quote_results: str = ""
    is_ev: str =""
    action: str =""
    clarifying_question: str =""
