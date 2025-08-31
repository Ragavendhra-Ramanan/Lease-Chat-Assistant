import pandas as pd
import numpy as np
from scipy import sparse
from sklearn.preprocessing import OneHotEncoder, RobustScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from datetime import datetime
import math
from typing import Optional

def _time_decay_weight(days_ago: np.ndarray, half_life: float = 30.0) -> np.ndarray:
    """Exponential decay weight: weight = 0.5 ** (days_ago / half_life)"""
    return 0.5 ** (days_ago / half_life)

def _normalize_scores(scores: np.ndarray) -> np.ndarray:
    if scores.max() - scores.min() > 0:
        return (scores - scores.min()) / (scores.max() - scores.min())
    return scores

class HybridConfig:
    k_final: int = 5
    k_similar_users: int = 5
    w_content: float = 0.4
    w_cf: float = 0.4
    w_simuser: float = 0.2
    history_alpha: float = 0.7
    recent_days_boost_half_life: float = 30.0
    normalize_component_scores: bool = True

class HybridRecommenderSystemWithClicks:
    def __init__(self, vehicles: pd.DataFrame, plans: pd.DataFrame, contracts: pd.DataFrame,
                 quotes: pd.DataFrame, clicks: Optional[pd.DataFrame] = None,
                 config: Optional[HybridConfig] = None):
        self.vehicles = vehicles.copy()
        self.plans = plans.copy()
        self.contracts = contracts.copy()
        self.quotes = quotes.copy()
        self.cfg = config or HybridConfig()
        self.today = datetime.now()
        self.contracts.rename(columns={"Customer ID":"User ID"},inplace=True)
        self.clicks = clicks.copy() if clicks is not None else pd.DataFrame(
            columns=["User ID", "Vehicle ID", "Product ID", "Clicked Date", "Rec Type"]
        )
        self._prepare_indices()
        self._build_content_encoders()
        self._build_behavior_matrices()
        self._fit_similar_user_index()

    def _prepare_indices(self):
        # Ensure IDs are strings
        self.vehicles["Vehicle ID"] = self.vehicles["Vehicle ID"].astype(str)
        self.plans["Product ID"] = self.plans["Product ID"].astype(str)
        self.contracts["User ID"] = self.contracts["User ID"].astype(str)
        self.contracts["Vehicle ID"] = self.contracts["Vehicle ID"].astype(str)
        self.contracts["Product ID"] = self.contracts["Product ID"].astype(str)
        self.quotes["User ID"] = self.quotes["User ID"].astype(str)
        self.quotes["Vehicle ID"] = self.quotes["Vehicle ID"].astype(str)
        self.quotes["Product ID"] = self.quotes["Product ID"].astype(str)
        self.vehicle_index = {vid: i for i, vid in enumerate(self.vehicles["Vehicle ID"].tolist())}
        self.plan_index = {pid: i for i, pid in enumerate(self.plans["Product ID"].tolist())}

    def _build_content_encoders(self):
        # Vehicles
        veh_struct_cols = [c for c in ["Year", "Price", "Mileage", "Horsepower"] if c in self.vehicles]
        veh_cat_cols = [c for c in ["Country", "Make", "Model", "Gear Type", "Fuel", "Preowned", "Currency"] if c in self.vehicles]
        self.veh_scaler = RobustScaler() if veh_struct_cols else None
        self.veh_ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=True) if veh_cat_cols else None
        parts = []
        if self.veh_scaler:
            parts.append(self.veh_scaler.fit_transform(self.vehicles[veh_struct_cols].fillna(0.0)))
        if self.veh_ohe:
            parts.append(self.veh_ohe.fit_transform(self.vehicles[veh_cat_cols].astype(str)))
        self.veh_content_matrix = sparse.hstack(parts).tocsr() if parts else sparse.csr_matrix((len(self.vehicles), 0))

        # Plans
        plan_struct_cols = [c for c in ["Lease Term"] if c in self.plans]
        plan_cat_cols = [c for c in ["Product Name","Flexi Lease","Tax Saving Plan","Renewal Cycle","Maintenance Type"] if c in self.plans]
        plan_text_col = "Short Description" if "Short Description" in self.plans else None
        self.plan_scaler = RobustScaler() if plan_struct_cols else None
        self.plan_ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=True) if plan_cat_cols else None
        self.plan_tfidf = TfidfVectorizer(max_features=20000, ngram_range=(1,2)) if plan_text_col else None
        parts = []
        if self.plan_scaler:
            parts.append(self.plan_scaler.fit_transform(self.plans[plan_struct_cols].fillna(0.0)))
        if self.plan_ohe:
            parts.append(self.plan_ohe.fit_transform(self.plans[plan_cat_cols].astype(str)))
        if self.plan_tfidf:
            parts.append(self.plan_tfidf.fit_transform(self.plans[plan_text_col].fillna("")))
        self.plan_content_matrix = sparse.hstack(parts).tocsr() if parts else sparse.csr_matrix((len(self.plans), 0))

    def _build_behavior_matrices(self):
        # Build user↔vehicle feedback from quotes/contracts
        q = self.quotes.copy()
        q["Days Ago"] = (self.today.replace(tzinfo=None) - pd.to_datetime(q["Created Date"]).dt.tz_localize(None)).dt.days.clip(lower=0)
        q["Decay"] = _time_decay_weight(q["Days Ago"].to_numpy(), self.cfg.recent_days_boost_half_life)
        q["Signal"] = 4 * q["Decay"]
        c = self.contracts.copy()
        c["Signal"] = 8.0
        fb = pd.concat([q[["User ID","Vehicle ID","Product ID","Signal"]], c[["User ID","Vehicle ID","Product ID","Signal"]]], ignore_index=True)
        self.feed=fb
        fb["User ID"] = fb["User ID"].astype(str)
        self.user_ids = sorted(fb["User ID"].unique().tolist())
        self.user_index = {uid:i for i, uid in enumerate(self.user_ids)}
        rows_u = fb["User ID"].map(self.user_index).to_numpy()
        cols_v = fb["Vehicle ID"].map(self.vehicle_index)
        cols_p = fb["Product ID"].map(self.plan_index)
        vals = fb["Signal"].to_numpy(dtype=float)
        valid_v = cols_v.notna()
        valid_p = cols_p.notna()
        self.user_vehicle_matrix = sparse.coo_matrix((vals[valid_v], (rows_u[valid_v], cols_v[valid_v].astype(int))),
                                                     shape=(len(self.user_ids), len(self.vehicles))).tocsr()
        self.user_plan_matrix = sparse.coo_matrix((vals[valid_p], (rows_u[valid_p], cols_p[valid_p].astype(int))),
                                                  shape=(len(self.user_ids), len(self.plans))).tocsr()
        self.user_vehicle_centroids = self._compute_user_centroids(self.user_vehicle_matrix, self.veh_content_matrix)
        self.user_plan_centroids = self._compute_user_centroids(self.user_plan_matrix, self.plan_content_matrix)

    @staticmethod
    def _compute_user_centroids(user_item: sparse.csr_matrix, item_content: sparse.csr_matrix) -> sparse.csr_matrix:
        row_sums = np.array(user_item.sum(axis=1)).ravel()
        row_sums[row_sums==0] = 1.0
        return sparse.diags(1.0/row_sums) @ user_item @ item_content

    def _fit_similar_user_index(self):
        if not self.user_ids:
            self.user_knn = None
            return
        veh_dense = self.user_vehicle_matrix.toarray()
        plan_dense = self.user_plan_matrix.toarray()
        user_vecs = np.hstack([veh_dense, plan_dense])
        self.user_knn = NearestNeighbors(n_neighbors=min(self.cfg.k_similar_users, max(1, user_vecs.shape[0]-1)), metric="cosine")
        self.user_knn.fit(user_vecs)
        self._user_vecs_cache = user_vecs

    def _cf_scores(self, user_id: str, item_matrix: sparse.csr_matrix, interactions: sparse.csr_matrix) -> np.ndarray:
        if self.user_knn is None or user_id not in self.user_index:
            return np.zeros(item_matrix.shape[0])
        uid = self.user_index[user_id]
        dist, idx = self.user_knn.kneighbors(self._user_vecs_cache[uid:uid+1], return_distance=True)
        sims = 1.0 - dist.ravel()
        neighbor_rows = interactions[idx.ravel(), :]
        scores = sims @ neighbor_rows.toarray()
        return scores

    def _content_scores(self, user_id: str, item_content: sparse.csr_matrix, user_centroid: sparse.csr_matrix) -> np.ndarray:
        if item_content.shape[1]==0:
            return np.zeros(item_content.shape[0])
        target = user_centroid
        A = item_content
        A_norm = np.sqrt(A.multiply(A).sum(axis=1)).A1 + 1e-9
        t_norm = math.sqrt((target.multiply(target)).sum()) + 1e-9
        dots = (A @ target.T).toarray().ravel()
        sims = dots / (A_norm * t_norm)
        return sims

    def _similar_user_popularity(self, user_id: str, item_type: str) -> np.ndarray:
        if self.user_knn is None or user_id not in self.user_index:
            return np.zeros(len(self.vehicles) if item_type=="Vehicle" else len(self.plans))
        uid = self.user_index[user_id]
        _, idx = self.user_knn.kneighbors(self._user_vecs_cache[uid:uid+1], return_distance=True)
        idx = idx.ravel()
        neigh_mat = self.user_vehicle_matrix[idx,:] if item_type=="Vehicle" else self.user_plan_matrix[idx,:]
        pop = neigh_mat.toarray().sum(axis=0)
        return _normalize_scores(pop)

    def recommend_vehicles_separate(self, user_id: str):
        """Return separate lists for content/cf/popularity scores, sorted by score descending."""
        user_row = self.user_index.get(str(user_id), None)
        user_centroid = self.user_vehicle_centroids[user_row:user_row+1] if user_row is not None else sparse.csr_matrix((1, self.veh_content_matrix.shape[1]))
        
        # Compute scores
        content = self._content_scores(user_id, self.veh_content_matrix, user_centroid)
        cf = self._cf_scores(user_id, self.veh_content_matrix, self.user_vehicle_matrix)
        pop = self._similar_user_popularity(user_id, "Vehicle")
        
        # Build sorted lists
        content_based = sorted(
            [{"Vehicle ID": vid, "score": float(score)} for vid, score in zip(self.vehicles["Vehicle ID"], content)],
            key=lambda x: -x["score"]
        )
        cf_based = sorted(
            [{"Vehicle ID": vid, "score": float(score)} for vid, score in zip(self.vehicles["Vehicle ID"], cf)],
            key=lambda x: -x["score"]
        )
        popularity_based = sorted(
            [{"Vehicle ID": vid, "score": float(score)} for vid, score in zip(self.vehicles["Vehicle ID"], pop)],
            key=lambda x: -x["score"]
        )
        
        return {
            "content_based": content_based,
            "cf_based": cf_based,
            "popularity_based": popularity_based,
        }
    def recommend_products_separate(self, user_id: str):
        """Return separate lists for content/cf/popularity scores for products, sorted by score descending."""
        user_row = self.user_index.get(str(user_id), None)
        user_centroid = self.user_plan_centroids[user_row:user_row+1] if user_row is not None else sparse.csr_matrix((1, self.plan_content_matrix.shape[1]))
        
        # Compute scores
        content = self._content_scores(user_id, self.plan_content_matrix, user_centroid)
        cf = self._cf_scores(user_id, self.plan_content_matrix, self.user_plan_matrix)
        pop = self._similar_user_popularity(user_id, "Product")
        
        # Build sorted lists
        content_based = sorted(
            [{"Product ID": pid, "score": float(score)} for pid, score in zip(self.plans["Product ID"], content)],
            key=lambda x: -x["score"]
        )
        cf_based = sorted(
            [{"Product ID": pid, "score": float(score)} for pid, score in zip(self.plans["Product ID"], cf)],
            key=lambda x: -x["score"]
        )
        popularity_based = sorted(
            [{"Product ID": pid, "score": float(score)} for pid, score in zip(self.plans["Product ID"], pop)],
            key=lambda x: -x["score"]
        )
        
        return {
            "content_based": content_based,
            "cf_based": cf_based,
            "popularity_based": popularity_based,
        }
    def recommend_top_vehicle_and_product(self, user_id: str, weights=(1.0, 1.0, 1.0)):
        """
        Recommend the top vehicle and product by combining content/cf/popularity scores,
        excluding items the user already contracted.
        Returns two plain strings: one for vehicle, one for product.
        """
        # Get separate recommendations
        veh_scores = self.recommend_vehicles_separate(user_id)
        prod_scores = self.recommend_products_separate(user_id)

        # --- Get list of contracted items for the user ---
        contracted_vehicles = set(self.contracts[self.contracts["User ID"] == str(user_id)]["Vehicle ID"].tolist())
        contracted_products = set(self.contracts[self.contracts["User ID"] == str(user_id)]["Product ID"].tolist())
        print(contracted_vehicles,"veh")
        # --- Combine vehicle scores and filter out contracted ---
        vehicle_df = pd.DataFrame({
            "Vehicle ID": [x["Vehicle ID"] for x in veh_scores["content_based"]],
            "content": [x["score"] for x in veh_scores["content_based"]],
            "cf": [x["score"] for x in veh_scores["cf_based"]],
            "popularity": [x["score"] for x in veh_scores["popularity_based"]],
        })
        vehicle_df["final_score"] = (
            weights[0]*vehicle_df["content"] + 
            weights[1]*vehicle_df["cf"] + 
            weights[2]*vehicle_df["popularity"]
        )
        vehicle_df = vehicle_df[~vehicle_df["Vehicle ID"].isin(contracted_vehicles)]
        if vehicle_df.empty:
            vehicle_str = "No recommended vehicles available."
        else:
            top_vehicle_id = vehicle_df.sort_values("final_score", ascending=False).iloc[0]["Vehicle ID"]
            top_vehicle = self.vehicles.loc[self.vehicles["Vehicle ID"] == top_vehicle_id, 
                                            ["Vehicle ID", "Make", "Model", "Year"]].iloc[0].to_dict()
            vehicle_str = (
                f"Recommended Vehicle (Based on Similar users with Contract):,\n"
                f"Vehicle ID: {top_vehicle['Vehicle ID']},\n"
                f"Make: {top_vehicle['Make']},\n"
                f"Model: {top_vehicle['Model']},\n"
                f"Year: {top_vehicle['Year']},"
            )

        # --- Combine product scores and filter out contracted ---
        product_df = pd.DataFrame({
            "Product ID": [x["Product ID"] for x in prod_scores["content_based"]],
            "content": [x["score"] for x in prod_scores["content_based"]],
            "cf": [x["score"] for x in prod_scores["cf_based"]],
            "popularity": [x["score"] for x in prod_scores["popularity_based"]],
        })
        product_df["final_score"] = (
            weights[0]*product_df["content"] + 
            weights[1]*product_df["cf"] + 
            weights[2]*product_df["popularity"]
        )
        product_df = product_df[~product_df["Product ID"].isin(contracted_products)]
        if product_df.empty:
            product_str = "No recommended products available."
        else:
            top_product_id = product_df.sort_values("final_score", ascending=False).iloc[0]["Product ID"]
            top_product = self.plans.loc[self.plans["Product ID"] == top_product_id, 
                                        ["Product ID", "Product Name", "Lease Term"]].iloc[0].to_dict()
            product_str = (
                f"Recommended Product(Based on Similar users with Contract):,\n"
                f"Product ID: {top_product['Product ID']},\n"
                f"Product Name: {top_product['Product Name']},\n"
                f"Lease Term: {top_product['Lease Term']},"
            )

        return vehicle_str, product_str
