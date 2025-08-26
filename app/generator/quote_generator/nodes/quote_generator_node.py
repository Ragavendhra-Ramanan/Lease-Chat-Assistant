from models.base_node import BaseNode
from models.agent_state import AgentState

class QuoteNode(BaseNode):
    """
    Async Quote Node: Calculates vehicle-product quote with adjustments.
    """
    async def run(self, state: AgentState):        
        # --- Take first vehicle candidate ---
        chosen_vehicle = state.quote_vehicle_candidates[0]
        state.quote_final_vehicle = chosen_vehicle

        # --- Base vehicle price and tax ---
        base_price = chosen_vehicle.get("Price", 0)
        tax = base_price * 0.1  # 10% tax

        chosen_product = state.quote_product_candidates[0]
        state.quote_final_product = chosen_product

        # --- Lease calculations ---
        lease_term = int(chosen_product.get("Lease Term", "12 months").split(" ")[0])  # months
        flexi_multiplier = 1.05 if chosen_product.get("Flexi Lease", "No").lower() == "yes" else 1.0
        tax_saving_discount = 0.95 if chosen_product.get("Tax Saving Plan", "No").lower() == "yes" else 1.0

        # Total product lease adjustment
        lease_adjustment = base_price * 0.02 * lease_term  # 2% per month
        base_price += lease_adjustment
        base_price *= flexi_multiplier * tax_saving_discount

        total_price = base_price + tax

        # --- Update state ---
        state.quote = {
            "vehicle": chosen_vehicle,
            "product": chosen_product,
            "base_price": base_price,
            "tax": tax,
            "total_price": total_price
        }

        state.quote_step = "quotation_end"
        state.quote_results = (
            f"Here’s your quote:\n"
            f"Vehicle: {chosen_vehicle.get('Make', '')} {chosen_vehicle.get('Model', '')} | "
            f"Base Price={chosen_vehicle.get('Price', 0)}\n"
            f"Product: {chosen_product.get('Product Name', 'None')}\n"
            f"Adjusted Price={base_price:.2f} | Tax={tax:.2f} | Total={total_price:.2f}"
        )
        return state
