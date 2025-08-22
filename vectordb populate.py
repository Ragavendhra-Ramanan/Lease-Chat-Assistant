import os
from dotenv import load_dotenv
import pandas as pd
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure

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

#Create collection
vehicles = client.collections.create(
    name="Vehicles",
    vector_config=Configure.Vectors.text2vec_weaviate(), #If using OpenAI vectorizer -> Configure.Vectors.text2vec_openai()
    #generative_config=Configure.Generative.openai()  # Configure the OpenAI generative AI integration
    
)

data = pd.read_csv("vehicle_data.csv")
vehicles = client.collections.get("Vehicles")

with vehicles.batch.fixed_size(batch_size=20) as batch:
    for _,d in data.iterrows():
        batch.add_object(
            {
                "Vehicle_ID": d["Vehicle ID"],
                "Country": d["Country"],
                "Make": d["Make"],
                "Model": d["Model"],
                "Year": d["Year"],
                "Mileage": d["Mileage"], 
                "Fuel": d["Fuel"],
                "Gear_type": d["Gear Type"],
                "Horsepower": d["Horsepower"],
                "Price": d["Price"],  
                "Currency": d["Currency"],
                "Preowned": d["Preowned"],
                "Inserted_date": d["Inserted date"]
            }
        )
        if batch.number_errors > 10:
            print("Batch import stopped due to excessive errors.")
            break

failed_objects = vehicles.batch.failed_objects
if failed_objects:
    print(f"Number of failed imports: {len(failed_objects)}")
    print(f"First failed object: {failed_objects[0]}")

client.close()