import pandas as pd

def get_most_popular(request_data, request_type, vehicles_df, products_df, quotes_df, contract_df, country=None):
    """
    Returns the most popular vehicle/product based on quotes or contracts.
    If country is specified, filters vehicles_df by country first.
    Returns a plain string.
    """
    # Filter vehicles by country if provided
    if request_data == "Vehicle" and country:
        vehicles_df = vehicles_df[vehicles_df["Country"] == country]

    if request_data == "Vehicle" and request_type == "quote":
        counts = quotes_df.groupby("Vehicle ID").size().reset_index(name="quote_count")
        merged = vehicles_df.merge(counts, on="Vehicle ID", how="left").fillna({"quote_count": 0})
        top_item = merged.sort_values("quote_count", ascending=False).head().sample(2).iloc[0]
        return f"Top Quoted Vehicle: {top_item['Vehicle ID']}, {top_item['Make']}, {top_item['Model']}, Year {top_item['Year']}"

    elif request_data == "Product" and request_type == "quote":
        counts = quotes_df.groupby("Product ID").size().reset_index(name="quote_count")
        merged = products_df.merge(counts, on="Product ID", how="left").fillna({"quote_count": 0})
        top_item = merged.sort_values("quote_count", ascending=False).head().sample(2).iloc[0]
        return f"Top Quoted Product: {top_item['Product ID']}, {top_item['Product Name']}, Lease Term {top_item['Lease Term']}"

    elif request_data == "Vehicle" and request_type == "contract":
        counts = contract_df.groupby("Vehicle ID").size().reset_index(name="contract_count")
        merged = vehicles_df.merge(counts, on="Vehicle ID", how="left").fillna({"contract_count": 0})
        top_item = merged.sort_values("contract_count", ascending=False).head().sample(2).iloc[0]
        return f"Top Contracted Vehicle: {top_item['Vehicle ID']}, {top_item['Make']}, {top_item['Model']}, Year {top_item['Year']}"

    elif request_data == "Product" and request_type == "contract":
        counts = contract_df.groupby("Product ID").size().reset_index(name="contract_count")
        merged = products_df.merge(counts, on="Product ID", how="left").fillna({"contract_count": 0})
        top_item = merged.sort_values("contract_count", ascending=False).head().sample(2).iloc[0]
        return f"Top Contracted Product: {top_item['Product ID']}, {top_item['Product Name']}, Lease Term {top_item['Lease Term']}"

def get_new_arrivals(request_type: str, vehicle_df, products_df, country=None):
    """
    Returns the latest inserted vehicle/product.
    Filters vehicles by country if provided.
    Returns a plain string.
    """
    if request_type == "Vehicle":
        if country:
            vehicle_df = vehicle_df[vehicle_df["Country"] == country]

        vehicle_df["Inserted Date"] = pd.to_datetime(vehicle_df["Inserted Date"])
        latest_vehicle = vehicle_df.sort_values("Inserted Date", ascending=False).head().sample(2).iloc[0]
        return f"Latest Vehicle: {latest_vehicle['Vehicle ID']}, {latest_vehicle['Make']}, {latest_vehicle['Model']}, Price {latest_vehicle['Price']}"

    else:
        products_df["Inserted Date"] = pd.to_datetime(products_df["Inserted Date"])
        latest_product = products_df.sort_values("Inserted Date", ascending=False).head().sample(2).iloc[0]
        return f"Latest Product: {latest_product['Product ID']}, {latest_product['Product Name']}, Lease Term {latest_product['Lease Term']}"
