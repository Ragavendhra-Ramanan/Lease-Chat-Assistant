from models.base_node import BaseNode
from models.agent_state import AgentState
import random
import pandas as pd
from datetime import datetime
import asyncio
import os
from utils.helper_functions import load_user_data_by_id 
class QuoteNode(BaseNode):
    """
    Async Quote Node: Calculates vehicle-product quote with adjustments.
    """
    async def run(self, state: AgentState, contract_df: pd.DataFrame,quote_df):        
        # --- Take first vehicle candidate ---
        user_data = load_user_data_by_id(state.customer_id)
        chosen_vehicle = state.quote_vehicle_candidates[0]
        state.quote_final_vehicle = chosen_vehicle

        # --- Take first product candidate ---
        chosen_product = state.quote_product_candidates[0]
        state.quote_final_product = chosen_product

        # --- Base vehicle price and tax ---
        base_price = chosen_vehicle.get("Price", 0)
        tax = base_price * 0.1  # 10% tax

        # --- Check if user is existing customer ---
        user_id = state.customer_id
        discount_applied = "No"
        if user_id in contract_df['Customer ID'].values:
            discount_rate = 0.10  # 10% discount
            discount_applied = "Yes"
        else:
            discount_rate = 0.0  # %0 discount

        discounted_price = base_price * (1 - discount_rate)

        # --- Flexi Lease and Tax Saving multipliers ---
        flexi_multiplier = 1.05 if chosen_product.get("Flexi Lease", "No").lower() == "yes" else 1.0
        tax_saving_discount = 0.95 if chosen_product.get("Tax Saving Plan", "No").lower() == "yes" else 1.0

        # Apply multipliers to discounted price
        adjusted_price = discounted_price * flexi_multiplier * tax_saving_discount

        # --- Lease calculations ---
        lease_term = int(chosen_product.get("Lease Term", 12))  # months
        percent_dict = {12:0.15, 24:0.20, 36:0.35, 48:0.40}
        quote_price = adjusted_price * percent_dict.get(lease_term, 0.2)  # depreciation factor
        emi = round((quote_price / lease_term) * random.uniform(1.05, 1.15), 2) 

        # --- Update state ---
        state.quote = {
            "vehicle": chosen_vehicle,
            "product": chosen_product,
            "base_price": base_price,
            "discounted_price": discounted_price,
            "adjusted_price": adjusted_price,
            "total_price": quote_price,
            "monthly_emi": emi,
            "discount_rate": discount_rate,
            "flexi_multiplier": flexi_multiplier,
            "tax_saving_discount": tax_saving_discount
        }

        state.quote_step = "quotation_end"
        quote_dict = await asyncio.to_thread(self.append_quote_row,quote_df,user_id,chosen_vehicle['Vehicle ID'],chosen_product['Product ID'],
                                     emi,quote_price,discount_applied)
        state.quote_results = (
            f"Here's your quote:\n"
            f"Name:{user_data['firstName']} {user_data['lastName']}\n"
            f"Contact: {user_data['email']} | {user_data['mobile']}\n"
            f"Created Date : {quote_dict['Created Date']}\n"
            f"Vehicle: {chosen_vehicle.get('Make', '')} {chosen_vehicle.get('Model', '')} | "
            f"Base Price={base_price:.2f} {chosen_vehicle['Currency']} \n"
            f"Product: {chosen_product.get('Product Name', 'None')}\n"
            f"Lease Term: {chosen_product['Lease Term']}\n"
            f"Discount Applied: {discount_rate*100:.0f}% \n "
            f"Adjusted Price={adjusted_price:.2f} {chosen_vehicle['Currency']}\n"
            f"Tax={tax:.2f} {chosen_vehicle['Currency']}\n" 
            f"Total={quote_price:.2f} {chosen_vehicle['Currency']}\n"
            f"Monthly EMI={emi} {chosen_vehicle['Currency']}\n"
            f"Quote Expiry= 30 days*"
        )
        return state
    def append_quote_row(
    self,
    quote_df: pd.DataFrame,
    customer_id: int,
    vehicle: dict,
    product: dict,
    emi: float,
    quote_price: float,
    discount_applied: bool,
    starting_quote_id: str = "Q1001"
) -> pd.DataFrame:
        """Append a new quote row with a unique Quote ID to quote_df."""

        # --- Generate unique Quote ID ---
        if not quote_df.empty:
            # Extract numeric part of existing Quote IDs
            existing_ids = quote_df['Quote ID'].str.extract(r'Q(\d+)', expand=False).astype(int)
            next_id_num = existing_ids.max() + 1
        else:
            next_id_num = int(starting_quote_id[1:])  # remove Q prefix

        quote_id = f"Q{next_id_num}"

        # --- Create new row ---
        created_date = datetime.utcnow()
        new_row = {
            "Quote ID": quote_id,
            "User ID": customer_id,
            "Vehicle ID": vehicle,
            "Product ID": product,
            "Monthly EMI": emi,
            "Quote Price": quote_price,
            "Created Date": created_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Discount Applied": "Yes" if discount_applied else "No"
        }

        # --- Append to quote_df ---
        quote_df = pd.concat([quote_df, pd.DataFrame([new_row])], ignore_index=True)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        quote_df.to_csv(os.path.join(base_dir,"../../../data/quote_data_new.csv"),index=False)
        return new_row
