from typing import Dict, Any
import pandas as pd
import os
base_dir = os.path.dirname(os.path.abspath(__file__))

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



