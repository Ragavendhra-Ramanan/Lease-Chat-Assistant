import os, json
from dotenv import load_dotenv
import weaviate
from weaviate.classes.init import Auth

load_dotenv()
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
    #additional_headers={
    #"X-OpenAI-Api-Key": "YOUR-OPENAI-API-KEY", # Replace with your OpenAI key
    #}
)

vehicles = client.collections.get("Vehicles")

#Vector (near text) search
response = vehicles.query.near_text(
    query="Honda automatic",
    limit=7
)

print("QUERY1 RESPONSE")
for obj in response.objects:
    print(json.dumps(obj.properties, indent=2))

print()

#Hybrid search
response2 = vehicles.query.hybrid(
    query="Toyota manual",  
    limit=2
)

print("QUERY2 RESPONSE")
for obj in response2.objects:
    print(json.dumps(obj.properties, indent=2))


client.close()