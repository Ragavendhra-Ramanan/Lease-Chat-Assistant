import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import Filter
import asyncio
from weaviate.classes.query import MetadataQuery


vectorizer_config = Configure.Vectors.text2vec_openai(
    model="text-embedding-3-small",  # embedding model
    type_="text",                     # type of input (text)
)


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

def create_vehicle_collection(client):
    client.collections.create(
        name="Vehicle",
        properties=[
            Property(name="Summary", data_type=DataType.TEXT, vectorize=True),
            Property(name="VehicleID", data_type=DataType.TEXT, vectorize=False),
        ],
        vector_config= vectorizer_config
    )
    return client.collections.get("Vehicle")

def create_product_collection(client):
    client.collections.create(
        name="Product",
        properties=[
            Property(name="Summary", data_type=DataType.TEXT, vectorize=True),
            Property(name="ProductID", data_type=DataType.TEXT, vectorize=False),
        ],
        vector_config=vectorizer_config
    )
    return client.collections.get("Product")

def create_contract_collection(client):
    client.collections.create(
        name="Contract",
        properties=[
            Property(name="Summary", data_type=DataType.TEXT, vectorize=True),
            Property(name="ContractID", data_type=DataType.NUMBER, vectorize=False),
            Property(name="CustomerID", data_type=DataType.NUMBER, vectorize=False),
            Property(name="VehicleID", data_type=DataType.TEXT, vectorize=False),
            Property(name="ProductID", data_type=DataType.TEXT, vectorize=False),
        ],
        vector_config=vectorizer_config
    )
    return client.collections.get("Contract")

def delete_collection(client,collection_name):
    try:
        client.collections.delete(collection_name)
        print("Collection " + collection_name + " deleted")
    except Exception as e:
        print("ERROR deleting collection:",collection_name)
        print(str(e))

def close_connection(client):
    client.close()

import asyncio
from weaviate.classes.query import Filter

async def async_query(collection, query=None, target_vector="default", filters=None,filter_val=None, limit=5,alpha: float = 0.5):
    # Build filter object if filters are provided
    filter_to_apply = None
    if (filters!=None):
        if(isinstance(filter_val,list)):
            filter_to_apply = Filter.by_property(filters).contains_any(filter_val)
        else:
            filter_to_apply = Filter.by_property(filters).equal(filter_val)

    # Run the synchronous query in a separate thread to keep async
    response =  await asyncio.to_thread(
        collection.query.hybrid,
        query=query,
        target_vector=target_vector,
        return_metadata=MetadataQuery(score=True, explain_score=True),
        filters=filter_to_apply,
        limit=limit,
        alpha=alpha   # mix factor between semantic and vector search
    )
    query_results = [obj.properties for obj in response.objects]
    return query_results
