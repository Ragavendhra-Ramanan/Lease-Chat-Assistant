from weaviate_operations import async_query
from weaviate_operations import connection_to_wcs, delete_collection, create_product_collection,create_contract_collection,create_vehicle_collection, close_connection
import os 
from dotenv import load_dotenv
import asyncio
load_dotenv()
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

client = connection_to_wcs(weaviate_url,weaviate_api_key,openai_api_key)
if(client):
    print("Connected to WCS instance")


async def run_sample():
    sample_query = "Honda Hatchback 2016"
    filters = "vehicleID"
    filter_value = ["V4000"]  # optional, can include multiple IDs
    vehicle_collection = client.collections.get("Vehicle")
    results = await async_query(vehicle_collection,
                                 query=sample_query,
                                 alpha=0.75, 
                                 filters=filters,
                                 filter_val=filter_value,
                                 limit=3)
    for obj in results.objects:
        print("VehicleID:", obj.properties.get("vehicleID"))
        print("Summary:", obj.properties.get("summary"))
        print("---")


if __name__ == "__main__":
    asyncio.run(run_sample())
    client.close()
