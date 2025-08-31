from sklearn.neighbors import NearestNeighbors
import numpy as np

def convert_to_customer(user_id,
                        request_type,
                        request_data,vehicle_index,
                        vehicle_matrix,
                        product_index,
                        product_matrix,vehicle_df,
                        product_df,
                        contract_df,quote_df):
        # 1. Get last quoted item for the user
        user_quotes = quote_df[quote_df['User ID'] == user_id]
        last_quote = user_quotes.sort_values('Created Date', ascending=False).iloc[0]
        last_vehicle_id = last_quote['Vehicle ID']
        last_product_id = last_quote['Product ID']
        last_vehicle = vehicle_df[vehicle_df["Vehicle ID"]==last_vehicle_id].iloc[0]
        last_product = product_df[product_df["Product ID"]==last_product_id].iloc[0]
        last_price = last_vehicle["Price"]  # last quoted price
        last_country = last_vehicle["Country"]
        last_lease_term = last_product["Lease Term"]  # last quoted price
        vehicle_id_list = contract_df["Vehicle ID"].tolist()
        product_id_list = contract_df["Product ID"].tolist()
        target_vehicle_embedding = vehicle_matrix[vehicle_index[last_vehicle_id]]
        if hasattr(target_vehicle_embedding, "toarray"):
                target_vehicle_embedding = target_vehicle_embedding.toarray()
        target_vehicle_embedding = np.asarray(target_vehicle_embedding).reshape(1, -1)


        target_product_embedding = product_matrix[product_index[last_product_id]]
        if hasattr(target_product_embedding, "toarray"):
                target_product_embedding = target_product_embedding.toarray()
        target_product_embedding = np.asarray(target_product_embedding).reshape(1, -1)

        if ((request_data=="Vehicle") and (request_type=="quote")):
                candidates = vehicle_df[
                (vehicle_df["Country"] == last_country) &
                (vehicle_df["Price"] <= last_price) &
                (vehicle_df["Vehicle ID"] != last_vehicle_id) 
                ]

                if candidates.empty:
                        return "No recommended vehicles found."

                candidates_embedding = vehicle_matrix[[vehicle_index[id] for id in candidates["Vehicle ID"]]]
                recommender_knn = NearestNeighbors(n_neighbors=1, metric="cosine")        
                recommender_knn.fit(candidates_embedding)
                idx = recommender_knn.kneighbors(target_vehicle_embedding, return_distance=False)[0][0]
                top_vehicle = candidates.iloc[idx]
                return (
                f"Recommended Vehicle (Last Quote with Better Price):\n"
                f"{top_vehicle['Vehicle ID']}\n"
                f"{top_vehicle['Make']}\n"
                f"{top_vehicle['Model']}\n"
                f"Price: {top_vehicle['Price']}\n"
                f"Country: {top_vehicle['Country']}"
                )

        elif ((request_data=="Product") and (request_type=="quote")):
                candidates = product_df[(product_df["Lease Term"] <= last_lease_term)
                                        &  (product_df["Product ID"] != last_product_id)]
                if candidates.empty:
                        return "No recommended products found."

                candidates_embedding = product_matrix[[product_index[id] for id in candidates["Product ID"]]]                
                recommender_knn = NearestNeighbors(n_neighbors=1, metric="cosine")
                recommender_knn.fit(candidates_embedding)

                idx = recommender_knn.kneighbors(target_product_embedding, return_distance=False)[0][0]
                top_product = candidates.iloc[idx]

                return (
                f"Recommended Product (Last Quote with Better Price):\n"
                f"{top_product['Product ID']}\n"
                f"{top_product['Product Name']}\n"
                f"Lease Term: {top_product['Lease Term']}"
                )


        elif ((request_data=="Vehicle") and (request_type=="contract")):
                candidates = vehicle_df[
                (vehicle_df["Vehicle ID"].isin(vehicle_id_list)) &
                (vehicle_df["Country"] == last_country) &
                (vehicle_df["Price"] <= last_price) &
                (vehicle_df["Vehicle ID"] != last_vehicle_id) 
                ]

                if candidates.empty:
                        return "No contracted vehicles found."

                candidates_embedding = vehicle_matrix[[vehicle_index[id] for id in candidates["Vehicle ID"]]]
                recommender_knn = NearestNeighbors(n_neighbors=1, metric="cosine")
                recommender_knn.fit(candidates_embedding)

                idx = recommender_knn.kneighbors(target_vehicle_embedding, return_distance=False)[0][0]
                top_vehicle = candidates.iloc[idx]

                return (
                f"Recommended Contract Vehicle (Last Quote with Better Price):\n"
                f" {top_vehicle['Vehicle ID']}\n"
                f"{top_vehicle['Make']}\n"
                f"{top_vehicle['Model']}\n"
                f"Price: {top_vehicle['Price']}\n"
                f"Country: {top_vehicle['Country']}"
                )


        elif ((request_data=="Product") and (request_type=="contract")):
                candidates = product_df[
                (product_df["Product ID"].isin(product_id_list)) &
                (product_df["Lease Term"] <= last_lease_term) &
                 (product_df["Product ID"] != last_product_id)
                ]

                if candidates.empty:
                        return "No contracted products found."

                candidates_embedding = product_matrix[[product_index[id] for id in candidates["Product ID"]]]
                recommender_knn = NearestNeighbors(n_neighbors=1, metric="cosine")
                recommender_knn.fit(candidates_embedding)

                idx = recommender_knn.kneighbors(target_product_embedding, return_distance=False)[0][0]
                top_product = candidates.iloc[idx]

                return (
                f"Recommended Contract Product (Last Quote with Better Price):\n"
                f"{top_product['Product ID']}\n"
                f"{top_product['Product Name']}\n"
                f"Lease Term: {top_product['Lease Term']}"
                )