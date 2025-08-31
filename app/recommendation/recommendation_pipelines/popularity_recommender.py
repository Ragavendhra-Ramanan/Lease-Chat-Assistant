import pandas as pd
def get_most_popular(request_data, request_type, vehicles_df, products_df, quotes_df, contract_df):

    if request_data == "Vehicle" and request_type == "quote":
        counts = quotes_df.groupby("Vehicle ID").size().reset_index(name="quote_count")
        merged = vehicles_df.merge(counts, on="Vehicle ID", how="left").fillna({"quote_count": 0})
        top_item = merged.sort_values("quote_count", ascending=False).iloc[0]

        markdown = f"**Top Quoted Vehicle:**\n- Make: {top_item['Make']}, Vehicle ID: {top_item['Vehicle ID']}, Model: {top_item['Model']}, Quotes: {int(top_item['quote_count'])}"
        return markdown

    elif request_data == "Product" and request_type == "quote":
        counts = quotes_df.groupby("Product ID").size().reset_index(name="quote_count")
        merged = products_df.merge(counts, on="Product ID", how="left").fillna({"quote_count": 0})
        top_item = merged.sort_values("quote_count", ascending=False).iloc[0]

        markdown = f"**Top Quoted Product:**\n- Product Name: {top_item['Product Name']}, Product ID: {top_item['Product ID']}, Lease Term: {top_item['Lease Term']}, Quotes: {int(top_item['quote_count'])}"
        return markdown

    elif request_data == "Vehicle" and request_type == "contract":
        counts = contract_df.groupby("Vehicle ID").size().reset_index(name="contract_count")
        merged = vehicles_df.merge(counts, on="Vehicle ID", how="left").fillna({"contract_count": 0})
        top_item = merged.sort_values("contract_count", ascending=False).iloc[0]

        markdown = f"**Top Contracted Vehicle:**\n- Make: {top_item['Make']}, Vehicle ID: {top_item['Vehicle ID']}, Model: {top_item['Model']}, Contracts: {int(top_item['contract_count'])}"
        return markdown

    elif request_data == "Product" and request_type == "contract":
        counts = contract_df.groupby("Product ID").size().reset_index(name="contract_count")
        merged = products_df.merge(counts, on="Product ID", how="left").fillna({"contract_count": 0})
        top_item = merged.sort_values("contract_count", ascending=False).iloc[0]

        markdown = f"**Top Contracted Product:**\n- Product Name: {top_item['Product Name']}, Product ID: {top_item['Product ID']}, Lease Term: {top_item['Lease Term']}, Contracts: {int(top_item['contract_count'])}"
        return markdown


def get_new_arrivals(request_type:str,vehicle_df,products_df):
    if(request_type=="Vehicle"):
        vehicle_df["Inserted Date"] = pd.to_datetime(vehicle_df["Inserted Date"])

        vehicle_df["Inserted Date"] = pd.to_datetime(vehicle_df["Inserted Date"])

        # Sort by Inserted Date descending
        df_sorted = vehicle_df.sort_values("Inserted Date", ascending=False)

        # Take first row
        first_vehicle = df_sorted.iloc[0]

        # Create Markdown string
        markdown_message = (
            f"**Latest Vehicle:**\n"
            f"- Vehicle ID: {first_vehicle['Vehicle ID']}\n"
            f"- Make: {first_vehicle['Make']}\n"
            f"- Model: {first_vehicle['Model']}\n"
            f"- Year: {first_vehicle['Year']}"
        )
    else:
        products_df["Inserted Date"] = pd.to_datetime(products_df["Inserted Date"])
        # Sort descending by insert_date
        products_sorted = products_df.sort_values("Inserted Date", ascending=False)
        # Take first row (latest inserted product)
        first_product = products_sorted.iloc[0]
        markdown_message = (
            f"**Latest Product:**\n"
            f"- Product ID: {first_product['Product ID']}\n"
            f"- Product Name: {first_product['Product Name']}\n"
            f"- Lease Term: {first_product['Lease Term']} months"
        )
    return markdown_message
