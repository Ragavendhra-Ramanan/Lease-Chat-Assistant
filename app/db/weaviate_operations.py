import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import Filter
import asyncio
from weaviate.classes.query import MetadataQuery


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
    # client.collections.create(
    #     name="Vehicle",
    #     properties=[
    #         Property(name="Summary", data_type=DataType.TEXT, vectorize=True),
    #         Property(name="VehicleID", data_type=DataType.TEXT, vectorize=False),
    #     ],
    #     vector_config= vectorizer_config
    # )
    # return client.collections.get("Vehicle")
    client.collections.create(
    name="Car",
    description="Vehicle dataset with details for leasing/recommendations",
    properties=[
        Property(name="vehicle_id", data_type=DataType.TEXT),
        Property(name="country", data_type=DataType.TEXT),
        Property(name="make", data_type=DataType.TEXT),
        Property(name="model", data_type=DataType.TEXT),
        Property(name="year", data_type=DataType.INT),
        Property(name="mileage", data_type=DataType.NUMBER),
        Property(name="fuel", data_type=DataType.TEXT),
        Property(name="gear_type", data_type=DataType.TEXT),
        Property(name="horsepower", data_type=DataType.INT),
        Property(name="price", data_type=DataType.INT),
        Property(name="currency", data_type=DataType.TEXT),
        Property(name="preowned", data_type=DataType.TEXT),
        Property(name="summary", data_type=DataType.TEXT),
    ],
    vectorizer_config=Configure.Vectorizer.text2vec_openai(),  # OpenAI embeddings
    )
    return client.collections.get("Car")


def create_product_collection(client):
    # client.collections.create(
    #     name="Product",
    #     properties=[
    #         Property(name="Summary", data_type=DataType.TEXT, vectorize=True),
    #         Property(name="ProductID", data_type=DataType.TEXT, vectorize=False),
    #     ],
    #     vector_config=vectorizer_config
    # )
    # return client.collections.get("Product")
    client.collections.create(
    name="Product",
    description="Leasing plans for vehicles",
    properties=[
        Property(name="product_id", data_type=DataType.TEXT),
        Property(name="product_name", data_type=DataType.TEXT),
        Property(name="short_description", data_type=DataType.TEXT),
        Property(name="lease_term", data_type=DataType.NUMBER),
        Property(name="flexi_lease", data_type=DataType.TEXT),
        Property(name="tax_saving_plan", data_type=DataType.TEXT),
        Property(name="renewal_cycle", data_type=DataType.TEXT),
        Property(name="maintenance_type", data_type=DataType.TEXT),
        Property(name="summary", data_type=DataType.TEXT),
    ],
    vectorizer_config=Configure.Vectorizer.text2vec_openai(),  # use OpenAI embeddings
    )
    return client.collections.get("Product")

def create_contract_collection(client):
    # client.collections.create(
    #     name="Contract",
    #     properties=[
    #         Property(name="Summary", data_type=DataType.TEXT, vectorize=True),
    #         Property(name="ContractID", data_type=DataType.NUMBER, vectorize=False),
    #         Property(name="CustomerID", data_type=DataType.NUMBER, vectorize=False),
    #         Property(name="VehicleID", data_type=DataType.TEXT, vectorize=False),
    #         Property(name="ProductID", data_type=DataType.TEXT, vectorize=False),
    #     ],
    #     vector_config=vectorizer_config
    # )
    # return client.collections.get("Contract")
    client.collections.create(
        name="Contract",
        vectorizer_config=Configure.Vectorizer.text2vec_openai(),  # OpenAI vectorization
        properties=[
            Property(name="ContractID", data_type=DataType.TEXT),
            Property(name="CustomerID", data_type=DataType.NUMBER),
            Property(name="ExistingCustomer", data_type=DataType.TEXT),
            Property(name="VehicleID", data_type=DataType.TEXT),
            Property(name="ProductID", data_type=DataType.TEXT),
            Property(name="MonthlyEMI", data_type=DataType.NUMBER),
            Property(name="ContractPrice", data_type=DataType.NUMBER),
            Property(name="LeaseStartDate", data_type=DataType.DATE),
            Property(name="LeaseExpiryDate", data_type=DataType.DATE),
            Property(name="RoadAssistance", data_type=DataType.TEXT),
            Property(name="Maintenance", data_type=DataType.TEXT),
            Property(name="DiscountApplied", data_type=DataType.TEXT),
            Property(name="Summary", data_type=DataType.TEXT),  # vectorized field
        ]
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

async def async_query(collection, query=None, filters=None,filter_val=None,where=[],
                       limit=5,alpha: float = 0.5):
    # Build filter object if filters are provided
    filter_to_apply = None
    if (filters!=None):
        if(isinstance(filter_val,list)):
            filter_to_apply = Filter.by_property(filters).contains_any(filter_val)
        else:
            filter_to_apply = Filter.by_property(filters).equal(filter_val)
    if where is not None:
        # If simple filter exists, combine with 'And'
        if filter_to_apply is not None:
            filter_to_apply = where.append(filter_to_apply)
        else:
            filter_to_apply =  where
    # Run the synchronous query in a separate thread to keep async
    response =  await asyncio.to_thread(
        collection.query.hybrid,
        query=query,
        return_metadata=MetadataQuery(score=True, explain_score=True),
        filters=filter_to_apply,
        limit=limit,
        alpha=alpha   # mix factor between semantic and vector search
    )
    query_results = [obj.properties for obj in response.objects]
    return query_results
