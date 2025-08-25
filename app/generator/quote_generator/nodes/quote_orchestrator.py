from models.base_node import BaseNode

class QuoteOrchestratorAgent(BaseNode):
    """
    Async Quote Orchestrator Agent:
    Routes the flow between vehicle filtering, product filtering, and quote generation.
    """

    async def run(self, state):
        # Extract current step and context
        step = state.get("quote_step")
        context = state.get("quote_context")

        # --- Initial or filtering in progress ---
        if step not in ("done", "quotation_end"):
            state["quote_next_agent"] = "filtering"

        # --- Vehicle filtering completed → move to product filtering ---
        elif step == "done" and context == "vehicle":
            state["quote_context"] = "product"
            state["quote_filters"] = {}
            state["quote_step"] = "product_name"  # start product filtering from first step
            state["quote_next_agent"] = "filtering"

        # --- Product filtering completed → move to quote generation ---
        elif step == "done" and context == "product":
            state["quote_context"] = "quote"
            state["quote_next_agent"] = "quote"

        # --- Quote generation finished → end ---
        elif step == "quotation_end":
            state["quote_next_agent"] = "end"

        return state
