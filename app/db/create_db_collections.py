import pandas as pd
from weaviate_operations import connection_to_wcs, delete_collection, create_product_collection,create_contract_collection,create_vehicle_collection, close_connection
import os 
from dotenv import load_dotenv
load_dotenv()
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = connection_to_wcs(weaviate_url,weaviate_api_key,openai_api_key)
if(client):
    print("Connected to WCS instance")

# 1. check vehicle data
collection_name = "Vehicle"
filename = "../data/vehicle_chunk_data.csv"
vehicle_df=pd.read_csv(filename)

delete_collection(client=client,collection_name=collection_name)

vehicle_collection = create_vehicle_collection(client=client)
for _, row in vehicle_df.iterrows():
    vehicle_collection.data.insert({
        "Summary": row["Summary"],
        "VehicleID": row["Vehicle ID"]
    })

# 2. leasing data
collection_name = "Product"
filename = "../data/leasing_chunk_data.csv"
product_df=pd.read_csv(filename)

delete_collection(client=client,collection_name=collection_name)

product_collection = create_product_collection(client=client)
for _, row in product_df.iterrows():
    product_collection.data.insert({
        "Summary": row["Summary"],
        "ProductID": row["Product ID"]
    })

# 3. contract data
collection_name = "Contract"
filename = "../data/customer_contract_data.csv"
contract_df=pd.read_csv(filename)

delete_collection(client=client,collection_name=collection_name)

contract_collection = create_contract_collection(client=client)
for _, row in contract_df.iterrows():
    contract_collection.data.insert({
        "Summary": row["Summary"],
        "ContractID": row["Contract ID"],
        "CustomerID": row["Customer ID"],
        "VehicleID": row["Vehicle ID"],
        "ProductID": row["Product ID"]
    })


close_connection(client=client)