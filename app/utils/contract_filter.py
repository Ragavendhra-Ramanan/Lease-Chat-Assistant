import re
from operator import eq, lt, le, gt, ge
import pandas as pd

op_map = {"=": eq, "<": lt, "<=": le, ">": gt, ">=": ge}


def parse_contract_string(contract_str: str):
    """
    Parse concatenated contract string into a dictionary.
    Handles date operators like >=, <=, >, <, = for start and expiry dates.
    """
    contract_dict = {}
    
    # Split by comma
    parts = contract_str.split(",")
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        key = key.strip()
        value = value.strip()
        
        # Handle date fields with operator
        if key in ["lease_start_date", "lease_expiry_date","monthly_emi"]:
            match = re.match(r"(<=|>=|<|>|=)?\s*(\d{4}-\d{2}-\d{2})", value)
            if match:
                op, date_val = match.groups()
                if not op:
                    op = "="
                contract_dict[key] = date_val
                contract_dict[key + "_op"] = op
        # Handle Yes/No fields
        elif key in ["maintenance", "existing_customer", "road_assistance", "discount_applied"]:
            contract_dict[key] = value
        # Otherwise keep as string
        else:
            contract_dict[key] = value

    return contract_dict

def filter_contract_data(filter_dict, df, customer_id):
    column_map = {
    "lease_start_date": "Lease Start Date",
    "lease_expiry_date": "Lease Expiry Date",
    "maintenance": "Maintenance",
    "monthly_emi": "Monthly EMI",
    "contract_id": "Contract ID",
    "discount_applied": "Discount Applied",
    "road_assistance" : "Road Assistance"
    }
    df = df[df["Customer ID"]==customer_id].copy()
    df["Lease Start Date"] = pd.to_datetime(df["Lease Start Date"]).dt.tz_convert(None)
    df["Lease Expiry Date"] = pd.to_datetime(df["Lease Expiry Date"]).dt.tz_convert(None)
    mask = pd.Series(True, index=df.index)

    for key, df_col in column_map.items():
        if key in filter_dict:
            # Handle date fields with operators
            if key in ["lease_start_date", "lease_expiry_date"]:
                op = filter_dict.get(key + "_op", "=")
                date_val = pd.to_datetime(filter_dict[key])
                mask &= (op_map[op](df[df_col], date_val))
            else:
                mask &= (df[df_col] == filter_dict[key])
    
    filtered_df = df[mask]
    
    # Convert filtered rows to list of dictionaries
    return filtered_df.to_dict(orient="records")
