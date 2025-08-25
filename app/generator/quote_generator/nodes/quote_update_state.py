from models.base_node import BaseNode
from models.agent_state import AgentState

class QuoteUpdateNode(BaseNode):
    """
    Async Quote Update Node:
    Updates the state based on user choice for vehicle or product filtering steps.
    """

    async def run(self, state:AgentState):
        context = state.quote_context  # vehicle or product
        step = state.quote_step
        user_choice = state.query

        # --- VEHICLE path ---
        if context == "vehicle":
            if step == "preowned":
                val = user_choice.strip().lower()
                if val in ["true", "yes", "y", "1"]:
                    state.quote_filters["Preowned"] = True
                elif val in ["false", "no", "n", "0"]:
                    state.quote_filters["Preowned"] = False
                state.quote_step = "make"

            elif step == "make":
                state.quote_filters["Make"] = user_choice
                state.quote_step = "price"

            elif step == "price":
                try:
                    min_p, max_p = map(int, user_choice.strip("()").split(","))
                    state.quote_filters["Price"] = (min_p, max_p)
                except:
                    state.quote_results = "Invalid price range format. Try again like (10000,20000)."
                state.quote_step = "country"

            elif step == "country":
                state.quote_filters["Country"] = user_choice
                state.quote_step = "model"

            elif step == "model":
                state.quote_filters["Model"] = user_choice
                state.quote_step = "year"

            elif step == "year":
                state.quote_filters["Year"] = int(user_choice.strip())
                state.quote_step = "vehicle_details"

            elif step == "vehicle_details":
                if user_choice.lower() == "yes":
                    state.quote_step = "done"
                else:
                    state.quote_results = "Okay, search cancelled."

        # --- PRODUCT path ---
        elif context == "product":
            if step == "product_name":
                state.quote_filters["Product Name"] = user_choice
                state.quote_step = "lease_term"

            elif step == "lease_term":
                state.quote_filters["Lease Term"] = user_choice
                state.quote_step = "flexi_lease"

            elif step == "flexi_lease":
                state.quote_filters["Flexi Lease"] = user_choice
                state.quote_step = "tax_saving_plan"

            elif step == "tax_saving_plan":
                state.quote_filters["Tax Saving Plan"] = user_choice
                state.quote_step = "renewal_cycle"

            elif step == "renewal_cycle":
                state.quote_filters["Renewal Cycle"] = user_choice
                state.quote_step = "maintenance_type"

            elif step == "maintenance_type":
                state.quote_filters["Maintenance Type"] = user_choice
                state.quote_step = "product_details"

            elif step == "product_details":
                if user_choice.lower() == "yes":
                    state.quote_step = "done"
                else:
                    state.quote_results = "Okay, search cancelled."

        return state
