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

# # 1. check vehicle data
# collection_name = "Car"
# filename = "../data/vehicle_data.csv"
# vehicle_df=pd.read_csv(filename)

# delete_collection(client=client,collection_name=collection_name)

# vehicle_collection = create_vehicle_collection(client=client)
# for _, row in vehicle_df.iterrows():
#     vehicle_collection.data.insert({
#         # "Summary": row["Summary"],
#         # "VehicleID": row["Vehicle ID"]
#         "vehicle_id": row["Vehicle ID"],
#           "country": row["Country"],
#             "make": row["Make"],
#             "model": row["Model"],
#             "year": row["Year"],
#             "mileage": row["Mileage"],
#             "fuel": row["Fuel"],
#             "gear_type": row["Gear Type"],
#             "horsepower": row["Horsepower"],
#             "price": row["Price"],
#             "currency": row["Currency"],
#             "preowned": row["Preowned"],
#             "inserted_date": str(row["Inserted Date"]),
#             "summary": row["Summary"],
#     })

# # 2. leasing data
# collection_name = "Product"
# filename = "../data/leasing_data.csv"
# product_df=pd.read_csv(filename)

# delete_collection(client=client,collection_name=collection_name)

# product_collection = create_product_collection(client=client)
# for _, row in product_df.iterrows():
#     product_collection.data.insert({
#         # "Summary": row["Summary"],
#         # "ProductID": row["Product ID"]
#          "product_id": row["Product ID"],
#         "product_name": row["Product Name"],
#         "short_description": row["Short Description"],
#         "lease_term": int(row["Lease Term"]),
#         "flexi_lease": row["Flexi Lease"],
#         "tax_saving_plan": row["Tax Saving Plan"],
#         "renewal_cycle": row["Renewal Cycle"],
#         "maintenance_type": row["Maintenance Type"],
#         "inserted_date": row["Inserted Date"],
#         "summary": row["Summary"],
#     })

# 3. contract data
collection_name = "Contract"
filename = "../data/contract_data.csv"
contract_df=pd.read_csv(filename)

delete_collection(client=client,collection_name=collection_name)

contract_collection = create_contract_collection(client=client)
for _, row in contract_df.iterrows():
    contract_collection.data.insert({
        # "Summary": row["Summary"],
        # "ContractID": row["Contract ID"],
        # "CustomerID": row["Customer ID"],
        # "VehicleID": row["Vehicle ID"],
        # "ProductID": row["Product ID"]
         "ContractID": row["Contract ID"],
            "CustomerID": row["Customer ID"],
            "ExistingCustomer": row["Existing Customer"],
            "VehicleID": row["Vehicle ID"],
            "ProductID": row["Product ID"],
            "MonthlyEMI": float(row["Monthly EMI"]),
            "LeaseStartDate": row["Lease Start Date"],
            "LeaseExpiryDate": row["Lease Expiry Date"],
            "RoadAssistance": row["Road Assistance"],
            "Maintenance": row["Maintenance"],
            "DiscountApplied": row["Discount Applied"],
            "PreferredCustomer": row["Preferred Customer"],
            "Summary": row["Summary"],
    })


close_connection(client=client)