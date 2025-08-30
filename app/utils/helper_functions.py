from typing import Dict, Any
import pandas as pd
import os
import csv

base_dir = os.path.dirname(os.path.abspath(__file__))
USER_CSV_FILE = os.path.join(base_dir,"../data/user_data.csv")
GUEST_USER_CSV_FILE = os.path.join(base_dir,"../data/guest_user_data.csv")

def inject_filters(query: str, filters: str, entity: str) -> str:
        """Turn natural-language filters into query modifiers."""
        if not filters:
            return query
        return f"{query}. Additionally filter {entity} records by: {filters}"

def get_data():
    vehicle_df = pd.read_csv(os.path.join(base_dir,"../data/vehicle_data.csv"))  # your dataset
    product_df = pd.read_csv(os.path.join(base_dir,"../data/leasing_data.csv"))  # your dataset
    contract_df = pd.read_csv(os.path.join(base_dir,"../data/contract_data.csv"))  # your dataset

    return vehicle_df, product_df, contract_df
def filter_df(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    for key, value in filters.items():
        if isinstance(value, tuple):  # numeric range
            df = df[(df[key] >= value[0]) & (df[key] <= value[1])]
        else:
            df = df[df[key] == value]
    return df

def load_user_data():
    # Ensure header is written only once
    if not os.path.exists(USER_CSV_FILE):
        df = pd.DataFrame(columns=["userId", "firstName", "lastName", "email", "mobile", "password", "country"])
        df.to_csv(USER_CSV_FILE, index=False)
    
    if not os.path.exists(GUEST_USER_CSV_FILE):
        df = pd.DataFrame(columns=["userId", "contact"])
        df.to_csv(GUEST_USER_CSV_FILE, index=False)