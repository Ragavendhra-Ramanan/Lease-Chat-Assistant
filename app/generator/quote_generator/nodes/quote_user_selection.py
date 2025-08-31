from models.base_node import BaseNode
from models.agent_state import AgentState
import pandas as pd
import json
class QuoteUserSelectionNode(BaseNode):
    """
    Async Filtering Node:
    Handles vehicle and product filtering based on current quote context and step.
    """

    def __init__(self, vehicle_df:pd.DataFrame, product_df, filter_df_func):
        """
        vehicle_df: Pandas DataFrame for vehicles
        product_df: Pandas DataFrame for products
        filter_df_func: function to filter a dataframe given filters
        """
        self.vehicle_df = vehicle_df
        self.vehicle_df.drop(columns="Summary",inplace=True)
        self.product_df = product_df
        self.product_df.drop(columns="Summary",inplace=True)
        self.product_df.drop(columns="Short Description",inplace=True)
        self.filter_df_func = filter_df_func

    async def run(self, state: AgentState):
        context = state.quote_context

        # --- VEHICLE filtering ---
        if context == "vehicle":
            df = self.filter_df_func(self.vehicle_df.copy(), state.quote_filters)            
            step = state.quote_step

            if len(df) == 1:
                state.quote_step = "vehicle_details"
                step = state.quote_step

            if step == "preowned":
                options = df["Preowned"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Do you want a Preowned vehicle?**\n\nOptions:\n{opts}"

            elif step == "make":
                options = df["Make"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Please choose a Make:**\n\n{opts}"

            elif step == "price":
                min_p, max_p = df["Price"].min(), df["Price"].max()
                print(min_p, max_p, "price")
                ranges = [(int(min_p), int((min_p + max_p) // 2)),
                          (int((min_p + max_p) // 2) + 1, int(max_p))]
                opts = "\n".join([f"- `{r}`" for r in ranges])
                state.quote_intermediate_results = f"**Select a Price Range:**\n\n{opts}\n\n*Format your answer like:* `(10000,20000)`"

            elif step == "country":
                options = df["Country"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Please choose a Country:**\n\n{opts}"

            elif step == "model":
                options = df["Model"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Please choose a Model:**\n\n{opts}"

            elif step == "year":
                options = df["Year"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Please choose a Year:**\n\n{opts}"

            elif step == "vehicle_details":
                state.quote_vehicle_candidates = df.to_dict(orient="records")
                formatted = json.dumps(state.quote_vehicle_candidates, indent=2)
                state.quote_intermediate_results = (
                    f"**Fetched the vehicle(s):**\n```json\n{formatted}\n```\n\n"
                    f"Proceed to **Lease plan Selection**? *(Yes/No)*"
                )

        # --- PRODUCT filtering ---
        elif context == "product":
            df = self.filter_df_func(self.product_df.copy(), state.quote_filters)
            
            step = state.quote_step
            print(df.shape, "products")
            if len(df) == 1:
                state.quote_step = "product_details"
                step = state.quote_step

            if step == "product_name":
                options = df["Product Name"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Please choose a Product:**\n\n{opts}"

            elif step == "lease_term":
                options = df["Lease Term"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Select Lease Term:**\n\n{opts}"

            elif step == "flexi_lease":
                options = df["Flexi Lease"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Flexi Lease available?**\n\nOptions:\n{opts}"

            elif step == "tax_saving_plan":
                options = df["Tax Saving Plan"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Tax Saving Plan required?**\n\nOptions:\n{opts}"

            elif step == "renewal_cycle":
                options = df["Renewal Cycle"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Please choose Renewal Cycle:**\n\n{opts}"

            elif step == "maintenance_type":
                options = df["Maintenance Type"].unique().tolist()
                opts = "\n".join([f"- `{o}`" for o in options])
                state.quote_intermediate_results = f"**Select Maintenance Type:**\n\n{opts}"

            elif step == "product_details":
                state.quote_product_candidates = df.to_dict(orient="records")
                state.quote_product_candidates = df.to_dict(orient="records")
                formatted = json.dumps(state.quote_product_candidates, indent=2)
                state.quote_intermediate_results = (
                    f"**Fetched the product(s):**\n```json\n{formatted}\n```\n\n"
                    f"Proceed to **Quote Generation**? *(Yes/No)*"
                )

        return state
