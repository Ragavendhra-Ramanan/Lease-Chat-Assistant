import pandas as pd
def get_most_popular(request_data, request_type, vehicles_df, products_df, quotes_df, contract_df):

    if request_data == "Vehicle" and request_type == "quote":
        counts = quotes_df.groupby("Vehicle ID").size().reset_index(name="quote_count")
        merged = vehicles_df.merge(counts, on="Vehicle ID", how="left").fillna({"quote_count": 0})
        top_item = merged.sort_values("quote_count", ascending=False).head().sample(2).iloc[0]

        markdown = f"**Top Quoted Vehicle:**\n-  {top_item['Vehicle ID']}, {top_item['Make']},{top_item['Model']}, Year {top_item['Year']}"
        return markdown

    elif request_data == "Product" and request_type == "quote":
        counts = quotes_df.groupby("Product ID").size().reset_index(name="quote_count")
        merged = products_df.merge(counts, on="Product ID", how="left").fillna({"quote_count": 0})
        top_item = merged.sort_values("quote_count", ascending=False).head().sample(2).iloc[0]

        markdown = f"**Top Quoted Product:**\n- {top_item['Product ID']}, {top_item['Product Name']}, Lease Term {top_item['Lease Term']}"
        return markdown

    elif request_data == "Vehicle" and request_type == "contract":
        counts = contract_df.groupby("Vehicle ID").size().reset_index(name="contract_count")
        merged = vehicles_df.merge(counts, on="Vehicle ID", how="left").fillna({"contract_count": 0})
        top_item = merged.sort_values("contract_count", ascending=False).head().sample(2).iloc[0]

        markdown = f"**Top Contracted Vehicle:**\n- {top_item['Make']}, {top_item['Vehicle ID']}, {top_item['Model']}, Year {top_item['Year']}"
        return markdown

    elif request_data == "Product" and request_type == "contract":
        counts = contract_df.groupby("Product ID").size().reset_index(name="contract_count")
        merged = products_df.merge(counts, on="Product ID", how="left").fillna({"contract_count": 0})
        top_item = merged.sort_values("contract_count", ascending=False).head().sample(2).iloc[0]

        markdown = f"**Top Contracted Product:**\n- {top_item['Product Name']}, {top_item['Product ID']}, Lease Term: {top_item['Lease Term']}"
        return markdown


def get_new_arrivals(request_type:str,vehicle_df,products_df):
    if(request_type=="Vehicle"):
        vehicle_df["Inserted Date"] = pd.to_datetime(vehicle_df["Inserted Date"])

        vehicle_df["Inserted Date"] = pd.to_datetime(vehicle_df["Inserted Date"])

        # Sort by Inserted Date descending
        df_sorted = vehicle_df.sort_values("Inserted Date", ascending=False)

        # Take first row
        first_vehicle = df_sorted.head().sample(2).iloc[0]

        # Create Markdown string
        markdown_message = (
            f"**Latest Vehicle:**\n"
            f"- {first_vehicle['Vehicle ID']}\n"
            f"- {first_vehicle['Make']}\n"
            f"-  {first_vehicle['Model']}\n"
            f"- Year {first_vehicle['Year']}"
        )
    else:
        products_df["Inserted Date"] = pd.to_datetime(products_df["Inserted Date"])
        # Sort descending by insert_date
        products_sorted:pd.DataFrame = products_df.sort_values("Inserted Date", ascending=False)
        # Take first row (latest inserted product)
        first_product = products_sorted.head().sample(2).iloc[0]
        markdown_message = (
            f"**Latest Product:**\n"
            f"-{first_product['Product ID']}\n"
            f"- {first_product['Product Name']}\n"
            f"- Lease Term {first_product['Lease Term']} "
        )
    return markdown_message
