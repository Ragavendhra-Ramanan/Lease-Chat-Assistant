import os, json
from dotenv import load_dotenv
import pandas as pd
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter

load_dotenv()
weaviate_url = os.getenv("WEAVIATE_URL")
weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

def connection_to_wcs(weaviate_url,weaviate_api_key,openai_api_key):
    try:
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            headers={"X-OpenAI-Api-Key": openai_api_key}
        )
        return client    
    except Exception as e:
        print("ERROR connecting to weaviate cloud instance")
        print(str(e))

def close_connection(client):
    client.close()

vehicle_properties,product_properties,contract_properties = [],[],[]   
vehicle_fields = ['Vehicle ID', 'Country', 'Make', 'Model', 'Year', 'Mileage', 'Fuel', 'Gear Type', 'Horsepower', 'Price', 'Currency', 'Preowned','Inserted Date']
product_fields = ['Product ID', 'Product Name', 'Short Description', 'Lease Term', 'Flexi Lease', 'Tax Saving Plan', 'Renewal Cycle', 'Maintenance Type', 'Inserted Date']
customer_contract_fields = ["Summary","Contract ID","Customer ID","Vehicle ID","Product ID"]

for i in vehicle_fields:
    if(i=="Year" or i=="Horsepower"):        
        vehicle_properties.append(Property(name='_'.join(i.split()), data_type=DataType.INT))
    elif(i=="Price"):            
        vehicle_properties.append(Property(name='_'.join(i.split()), data_type=DataType.NUMBER))
    else:
        vehicle_properties.append(Property(name='_'.join(i.split()), data_type=DataType.TEXT))

for i in product_fields:
    product_properties.append(Property(name='_'.join(i.split()), data_type=DataType.TEXT))

for i in customer_contract_fields:
    if(i=="Contract ID" or i=="Customer ID"):        
        contract_properties.append(Property(name='_'.join(i.split()), data_type=DataType.INT))
    else:
        contract_properties.append(Property(name='_'.join(i.split()), data_type=DataType.TEXT))

collections = ["Vehicles","Products","Customer_Contracts"]
collection_properties = {i:j for(i,j) in zip(collections,[vehicle_properties,product_properties,contract_properties])}

def create_collection(client,collection_name,fields):
    try:
        exists = client.collections.exists(collection_name)
        if(exists):
            raise Exception("Collection already exists")
        
        collection = client.collections.create(
                    name=collection_name, 
                    properties=collection_properties[collection_name], 
                    vector_config=Configure.Vectors.text2vec_openai(
                        source_properties=fields,
                        model="ada",
                        model_version="002",
                        type_="text"
                    )       
        )    
        if(collection):            
            print("Collection " + collection_name + " created")
    except Exception as e:
        print("ERROR creating collection:",collection_name)
        print(str(e))

def add_data_to_collection(client,filename,collection_name,fields):
    collection_data = None
    try:
        data = pd.read_csv(filename)
        collection_data = client.collections.get(collection_name)

        with collection_data.batch.fixed_size(batch_size=20) as batch:
            for _,d in data.iterrows():
                data_object = {'_'.join(i.split()):d[i] for i in fields}
                batch.add_object(data_object)
                if batch.number_errors > 10:
                    raise Exception("Batch import stopped due to excessive errors.")
        
        print("Data added to " + collection_name+ " collection")

    except Exception as e:
        print("ERROR on adding data to collection:",collection_name)
        print(str(e))
        failed_objects = collection_data.batch.failed_objects
        if failed_objects:
            print(f"Number of failed imports: {len(failed_objects)}")
            print(f"First failed object: {failed_objects[0]}")

def get_collection(client,collection_name):
    try:
        collection_data = client.collections.get(collection_name)
        return collection_data
    except Exception as e:
        print("ERROR on retrieving collection:",collection_name)
        print(str(e))   

def query_collection(client,collection_name,input_query,lim,filters=None,filter_val=None,filter_type=None):
    try:    
        collection_data = client.collections.get(collection_name)
        filter_to_apply = None
        if (filters!=None and filter_val!=None):
            if(filter_type=="list"):
                    id_list =['vehicle_ID','product_ID','customer_ID','contract_ID']
                    if(len(filter_val)<1):
                        filter_val = [0] if(id_list.index(filters)>1) else ["None"]
                    filter_to_apply = Filter.by_property(filters).contains_any(filter_val)
            else:
                filter_to_apply = Filter.by_property(filters).equal(filter_val)

        response = collection_data.query.hybrid(
            query=input_query,  
            limit=lim,
            filters = filter_to_apply        
        )

        print("QUERY RESPONSE") 
        query_results = [obj.properties for obj in response.objects]
        return query_results if(len(query_results)) else None

    except Exception as e:
        print("ERROR on querying collection:",collection_name)
        print(str(e))

def display_query_results(query_results):
    results = ""
    for i in query_results:
        res = json.dumps(i, indent=2)
        results = results + ",\n" + res
    return results[1:].strip()

def delete_collection(client,collection_name):
    try:
        client.collections.delete(collection_name)
        print("Collection " + collection_name + " deleted")
    except Exception as e:
        print("ERROR deleting collection:",collection_name)
        print(str(e))

"""
client = connection_to_wcs(weaviate_url,weaviate_api_key,openai_api_key)
if(client):
    print("Connected to WCS instance")

collection_name = "Vehicles"
filename = "vehicle_data.csv"
create_collection(client,collection_name,vehicle_fields)
add_data_to_collection(client,filename,collection_name,vehicle_fields)

#input_query = "Toyota manual"
#query_collection(client,collection_name,input_query,lim,filters=None)

collection_name = "Products"
filename = "leasing_data.csv"
create_collection(client,collection_name,product_fields)
add_data_to_collection(client,filename,collection_name,product_fields)

#input_query = "Maruti Lease Plan with flexi lease"
#query_collection(client,collection_name,input_query,lim,filters=None)

collection_name = "Customer_Contracts"
filename = "customer_contract_data.csv"
create_collection(client,collection_name,customer_contract_fields)
add_data_to_collection(client,filename,collection_name,customer_contract_fields)

#input_query = "Existing customer contracts for more than 24 months"
#query_collection(client,collection_name,input_query,lim,filters=None)

close_connection(client)
print("Connection to WCS instance closed")
"""

"""
vehicle_query = "Toyota manual"
product_query = "Maruti Lease Plan with flexi lease"
vehicle_ids = ["V4080","V4034","V4067"]  #["v0","-v1"]
product_ids = ['P1010','P1007'] #['P7010','P1111']

vehicle_results = query_collection(client,collection_name="Vehicles",input_query=vehicle_query,lim=5,filters="vehicle_ID",filter_val=vehicle_ids,filter_type="list")   
product_results = query_collection(client,collection_name="Products",input_query=product_query,lim=5,filters="product_ID",filter_val=product_ids,filter_type="list") 
print(display_query_results(vehicle_results))
print("\n")
print(display_query_results(product_results))
print("\n")

client = connection_to_wcs(weaviate_url,weaviate_api_key,openai_api_key)
if(client):
    print("Connected to WCS instance")
contract_query = "Existing customer contracts for more than 24 months"
filters="Customer_ID"
contract_filters = {"customer_id":1808}
contract_results = query_collection(client,collection_name="Customer_Contracts",input_query=contract_query,lim=5,filters="customer_ID",filter_val=contract_filters["customer_id"])
print(contract_results)
print(display_query_results(contract_results))

close_connection(client)
print("Connection to WCS instance closed")

res = [{'summary': 'Contract 234: Lease of Vehicle V4089 under Product P2018 for 24 months, EMI 322 USD, Road Assistance: no, Maintenance: yes, Existing Customer: yes, Discount Applied: no, Preferred Customer: no', 'customer_ID': 1808, 'product_ID': 'P2018', 'contract_ID': 234, 'vehicle_ID': 'V4089'}, {'summary': 'Contract 36: Lease of Vehicle V4005 under Product P2012 for 36 months, EMI 552 USD, Road Assistance: no, Maintenance: no, Existing Customer: yes, Discount Applied: no, Preferred Customer: no', 'customer_ID': 1808, 'product_ID': 'P2012', 'contract_ID': 36, 'vehicle_ID': 'V4005'}]
print(display_query_results(res))
"""