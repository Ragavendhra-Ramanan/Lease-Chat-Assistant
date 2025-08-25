from models.base_node import BaseNode

class QuoteUserSelectionNode(BaseNode):
    """
    Async Filtering Node:
    Handles vehicle and product filtering based on current quote context and step.
    """

    def __init__(self, vehicle_df, product_df, filter_df_func):
        """
        vehicle_df: Pandas DataFrame for vehicles
        product_df: Pandas DataFrame for products
        filter_df_func: function to filter a dataframe given filters
        """
        self.vehicle_df = vehicle_df
        self.product_df = product_df
        self.filter_df_func = filter_df_func

    async def run(self, state):
        context = state.get("quote_context")

        # --- VEHICLE filtering ---
        if context == "vehicle":
            df = self.filter_df_func(self.vehicle_df.copy(), state.get('quote_filters', {}))
            
            step = state.get('quote_step')

            if step == "preowned":
                options = df["Preowned"].unique().tolist()
                state["quote_results"] = f"Do you want a Preowned vehicle? Options: {options}"

            elif step == "make":
                options = df["Make"].unique().tolist()
                state["quote_results"] = f"Please choose a Make: {options}"

            elif step == "price":
                min_p, max_p = df["Price"].min(), df["Price"].max()
                ranges = [(int(min_p), int((min_p+max_p)//2)),
                          (int((min_p+max_p)//2)+1, int(max_p))]
                state["quote_results"] = f"Select a Price Range: {ranges}"

            elif step == "country":
                options = df["Country"].unique().tolist()
                state["quote_results"] = f"Please choose a Country: {options}"

            elif step == "model":
                options = df["Model"].unique().tolist()
                state["quote_results"] = f"Please choose a Model: {options}"

            elif step == "year":
                options = df["Year"].unique().tolist()
                state["quote_results"] = f"Please choose a Year: {options}"

            elif step == "vehicle_details":
                state['quote_vehicle_candidates'] = df.to_dict(orient="records")
                state["quote_results"] = (
                    f"Fetched the vehicle(s): {state['quote_vehicle_candidates']}. "
                    "Proceed to Lease plan Selection [Yes/No]"
                )

        # --- PRODUCT filtering ---
        elif context == "product":
            df = self.filter_df_func(self.product_df.copy(), state.get('quote_filters', {}))
            
            step = state.get('quote_step')

            if step == "product_name":
                options = df["Product Name"].unique().tolist()
                state["quote_results"] = f"Please choose a Product: {options}"

            elif step == "lease_term":
                options = df["Lease Term"].unique().tolist()
                state["quote_results"] = f"Select Lease Term: {options}"

            elif step == "flexi_lease":
                options = df["Flexi Lease"].unique().tolist()
                state["quote_results"] = f"Flexi Lease available? Options: {options}"

            elif step == "tax_saving_plan":
                options = df["Tax Saving Plan"].unique().tolist()
                state["quote_results"] = f"Tax Saving Plan required? Options: {options}"

            elif step == "renewal_cycle":
                options = df["Renewal Cycle"].unique().tolist()
                state["quote_results"] = f"Please choose Renewal Cycle: {options}"

            elif step == "maintenance_type":
                options = df["Maintenance Type"].unique().tolist()
                state["quote_results"] = f"Select Maintenance Type: {options}"

            elif step == "product_details":
                state['quote_product_candidates'] = df.to_dict(orient="records")
                state["quote_results"] = (
                    f"Fetched the product(s): {state['quote_product_candidates']}. "
                    "Proceed to Quote Generation [Yes/No]"
                )

        return state
