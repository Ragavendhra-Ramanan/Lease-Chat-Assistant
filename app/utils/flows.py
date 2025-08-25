from generator.quote_generator.nodes.quote_orchestrator import QuoteOrchestratorAgent
from search.contract_search.nodes.contract_search_node import ContractNode
from search.vehicle_search.nodes.vehicle_search_node import VehicleNode
from search.product_search.nodes.product_search_node import ProductNode
from search.other_search.nodes.other_search_node import GeneralSearchNode
ROUTE_MAP = {
    "quotation": QuoteOrchestratorAgent,
    "contract": ContractNode,
    "product": ProductNode,
    "vehicle": VehicleNode,
    "general": GeneralSearchNode,
}