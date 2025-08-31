import pandas as pd
import asyncio
from .recommendation_pipelines.search_recommender import static_search_recommendation
from .recommendation_pipelines.popularity_recommender import get_most_popular, get_new_arrivals
from .recommendation_pipelines.customer_conversion_recommender import convert_to_customer
from .recommendation_pipelines.customer_retention_recommender import HybridRecommenderSystemWithClicks
from conversation_intents.extract_conversation_intent import load_user_preferences_dict
from utils.helper_functions import get_data
import os
def get_quote_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    quote_df = pd.read_csv(os.path.join(base_dir,"../data/quote_data_new.csv"))
    return quote_df

vehicle_df, product_df, contract_df, guest_df = get_data()
hybrid_recommender = HybridRecommenderSystemWithClicks(vehicles=vehicle_df,
                                                       plans=product_df,
                                                       contracts=contract_df,
                                                       quotes=get_quote_data())

async def get_customer_preference_by_hybrid(user_id,request_type):
    results =await asyncio.to_thread(
        hybrid_recommender.recommend_top_vehicle_and_product,
        user_id
    )
    if(request_type == "Vehicle"):
        return results[0]
    else:
        return results[1]
async def get_preferences_by_search(client,user_id,request_type):
    vehicle_prefs = load_user_preferences_dict(user_id=user_id, types="Vehicle")
    product_prefs = load_user_preferences_dict(user_id=user_id, types="Product")
    search_preferences = await static_search_recommendation(
                                client=client,
                                vehicle_pref=vehicle_prefs["unstructured_vehicle"],
                                vehicle_structured_likes=vehicle_prefs["structured_vehicle"],
                                vehicle_dislike=vehicle_prefs["dislike_unstructured_vehicle"],
                                vehicle_structured_dislikes=vehicle_prefs["dislike_structured_vehicle"],
                                product_pref=product_prefs["unstructured_product"],
                                product_structured_likes=product_prefs["structured_product"],
                                product_dislike=product_prefs["dislike_unstructured_product"],
                                product_structured_dislikes=product_prefs["dislike_structured_product"],
                                alpha=0.5
                                )
    if (request_type=="Vehicle"):
        return search_preferences["vehicles"]
    else:
        return search_preferences["products"]

async def get_preferences_by_popularity(
        request_type,
        request_data,
        country):
    quote_df = await asyncio.to_thread(get_quote_data)
    popularity_preferences = await asyncio.to_thread(
        get_most_popular,
        request_data,
        request_type,
        vehicle_df,
        product_df,
        quote_df,
        contract_df,
        country
    )
    return popularity_preferences

async def get_preferences_by_date(request_type,country):
    preferences = await asyncio.to_thread(
        get_new_arrivals,
        request_type,
        vehicle_df,
        product_df,
        country
    )
    return preferences

async def get_preferences_for_customer_conversion(user_id,request_type,request_data):
    quote_df = await asyncio.to_thread(get_quote_data)
    conversion_preferences = await asyncio.to_thread(
        convert_to_customer,
        user_id,
        request_type,
        request_data,
        hybrid_recommender.vehicle_index,
        hybrid_recommender.veh_content_matrix,
        hybrid_recommender.plan_index,
        hybrid_recommender.plan_content_matrix,
        vehicle_df,
        product_df,
        contract_df,
        quote_df
    )
    return conversion_preferences

async def get_preferences_for_customer(user_id):
    vehicle_preference = await asyncio.to_thread(
        hybrid_recommender.recommend_vehicles_separate,
        user_id
    )
    product_preference = await asyncio.to_thread(
            hybrid_recommender.recommend_products_separate,
            user_id
    )
    return [vehicle_preference,product_preference]


async def get_new_user_recommendation(country):
    preference_1= await get_preferences_by_popularity(request_data="Vehicle",request_type="contract",country=country)
    preference_2= await get_preferences_by_date(request_type="Vehicle",country=country)
    preference_3= await get_preferences_by_popularity(request_data="Product",request_type="quote",country=country)
    return [preference_1,preference_2,preference_3]

async def get_potential_customer_recommendation(user_id,client):
    preference_1 = await get_preferences_for_customer_conversion(user_id,request_data="Vehicle",request_type="quote")
    preference_2 = await get_preferences_for_customer_conversion(user_id=user_id,request_data="Product",request_type="contract")
    preference_3 = await get_preferences_by_search(client,user_id,"Vehicle")
    return [preference_1,preference_2,preference_3]

async def get_potential_user_engagement_recommendation(client,user_id,country):
    preference_1 = await get_preferences_by_search(client,user_id,"Vehicle")
    preference_2 = await get_preferences_by_search(client,user_id,"Product")
    preference_3= await get_preferences_by_date(request_type="Vehicle",country=country)
    return [preference_1,preference_2,preference_3]

async def get_customer_retention_recommendation(client,user_id):
    preference_1 = await get_customer_preference_by_hybrid(user_id,"Vehicle")
    preference_2 = await get_customer_preference_by_hybrid(user_id,"Product")
    preference_3 = await get_preferences_by_search(client,user_id,"Vehicle")
    return [preference_1,preference_2,preference_3]
