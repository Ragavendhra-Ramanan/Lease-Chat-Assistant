import asyncio
from datetime import datetime, timezone
from weaviate.classes.query import MetadataQuery
from weaviate.collections.classes.filters import Filter
from rapidfuzz import fuzz


def time_decay_weight(ts, half_life_days: float = 30.0):
    if ts is None:
        return 1.0
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    days = (datetime.now(timezone.utc) - ts).days
    return 0.5 ** (days / half_life_days)

def combine_preferences(preferences):
    return " ".join(p["query"] for p in preferences if "query" in p)


def build_structured_filters(structured_pref: list):
    filters = []
    for p in structured_pref:
        field, val = p["field"], p["value"]
        if str(val).startswith("<"):
            filters.append(Filter.by_property(field).less_than(float(val[1:])))
        elif str(val).startswith(">"):
            filters.append(Filter.by_property(field).greater_than(float(val[1:])))
        elif str(val).startswith("="):
            filters.append(Filter.by_property(field).equal(float(val[1:])))
        else:
            filters.append(Filter.by_property(field).equal(int(val)))
    if not filters:
        return None
    f = filters[0]
    for flt in filters[1:]:
        f = f | flt
    return f
def apply_advanced_scoring(results,
                           likes, dislikes,
                           structured_likes=[], structured_dislikes=[]):
    ranked = []
    for r in results:
        base_score = r["metadata"].score
        text_blob = str(r["properties"]).lower()

        # ---- Text likes ----
        like_boost = 1.0
        for l in likes:
            decay = time_decay_weight(l.get("timestamp"))
            score = fuzz.partial_ratio(text_blob, l["query"].lower()) / 100.0
            like_boost += decay *score

        # ---- Fuzzy text dislikes ----
        dislike_penalty = 1.0
        for d in dislikes:
            decay = time_decay_weight(d.get("timestamp"))
            score = fuzz.partial_ratio(text_blob, d["query"].lower()) / 100.0
            dislike_penalty -= 0.5 * decay * score
        dislike_penalty = max(dislike_penalty, 0.1)

        # ---- Structured likes ----
        for s in structured_likes:
            decay = time_decay_weight(s.get("timestamp"))
            field_val = r["properties"].get(s["field"], None)
            # Skip if value is missing
            if field_val is None:
                continue
            # Convert to float if numeric
            try:
                field_val = float(field_val)
            except ValueError:
                field_val = str(field_val).lower()

            raw_val = str(s["value"])
            op, val = None, None

            if raw_val.startswith("<"):
                op, val = "<", float(raw_val[1:])
            elif raw_val.startswith(">"):
                op, val = ">", float(raw_val[1:])
            elif raw_val.startswith("="):
                op, val = "=", float(raw_val[1:])
            else:
                # fallback for categorical string match
                val = raw_val.lower()

            match = False
            if op == "<" and isinstance(field_val, float):
                match = field_val < val
            elif op == ">" and isinstance(field_val, float):
                match = field_val > val
            elif op == "=" and isinstance(field_val, float):
                match = field_val == val
            elif isinstance(field_val, str):
                match = val in field_val

            if match:
                like_boost += decay 

        # ---- Structured dislikes ----
        for s in structured_dislikes:
            decay = time_decay_weight(s.get("timestamp"))
            field_val = r["properties"].get(s["field"], None)
            if field_val is None:
                continue
            try:
                field_val = float(field_val)
            except ValueError:
                field_val = str(field_val).lower()

            raw_val = str(s["value"])
            op, val = None, None
            if raw_val.startswith("<"):
                op, val = "<", float(raw_val[1:])
            elif raw_val.startswith(">"):
                op, val = ">", float(raw_val[1:])
            elif raw_val.startswith("="):
                op, val = "=", float(raw_val[1:])
            else:
                val = raw_val.lower()

            match = False
            if op == "<" and isinstance(field_val, float):
                match = field_val < val
            elif op == ">" and isinstance(field_val, float):
                match = field_val > val
            elif op == "=" and isinstance(field_val, float):
                match = field_val == val
            elif isinstance(field_val, str):
                match = val in field_val

            if match:
                dislike_penalty -= 0.5 * decay

            dislike_penalty = max(dislike_penalty, 0.1)


        # ---- Final score ----
        r["final_score"] = base_score * like_boost * dislike_penalty
        ranked.append(r)

    return sorted(ranked, key=lambda x: x["final_score"], reverse=True)

async def static_search_recommendation(
    client,
    vehicle_pref, vehicle_dislike, vehicle_structured_likes, vehicle_structured_dislikes,
    product_pref, product_dislike, product_structured_likes, product_structured_dislikes,
    limit=5, alpha=0.5
):
    results = {}

    # --- Vehicles ---
    if vehicle_pref:
        vehicle_query = combine_preferences(vehicle_pref)
        vehicle_filter = build_structured_filters(vehicle_structured_likes + vehicle_structured_dislikes)
        print(vehicle_query,vehicle_filter,"ghbj")
        v_resp = await asyncio.to_thread(
            client.collections.get("Car").query.hybrid,
            query=vehicle_query,
            return_metadata=MetadataQuery(score=True),
            limit=limit*3,
            alpha=alpha,
            filters=vehicle_filter
        )
        v_clean = [{"properties": obj.properties, "metadata": obj.metadata} for obj in v_resp.objects]
        v_ranked = apply_advanced_scoring(v_clean, vehicle_pref, vehicle_dislike,
                                        structured_likes=vehicle_structured_likes,
                                        structured_dislikes=vehicle_structured_dislikes)
        top_vehicle= v_ranked[0]
        results["vehicles"] = f"""**Recommended Based on Search:**
                        - Vehicle ID: {top_vehicle["properties"]['vehicle_id']}
                        - Make: {top_vehicle["properties"]['make']}  
                        - Model: {top_vehicle["properties"]['model']}  
                        - Price: {top_vehicle["properties"]['price']}  
                        - Country: {top_vehicle["properties"]['country']}  
                        """
    if product_pref:
        # --- Products ---
        product_query = combine_preferences(product_pref)
        product_filter = build_structured_filters(product_structured_likes + product_structured_dislikes)
        p_resp = await asyncio.to_thread(
            client.collections.get("Product").query.hybrid,
            query=product_query,
            return_metadata=MetadataQuery(score=True),
            limit=limit*3,
            alpha=alpha,
            filters=product_filter
        )
        p_clean = [{"properties": obj.properties, "metadata": obj.metadata} for obj in p_resp.objects]
        p_ranked = apply_advanced_scoring(p_clean, product_pref, product_dislike,
                                        structured_likes=product_structured_likes,
                                        structured_dislikes=product_structured_dislikes)
        top_product = p_ranked[0]
        results["products"] = f"""**Recommended Based on Search:**
                        - Product ID: {top_product["properties"]['product_id']}  
                        - Product Name: {top_product["properties"]['product_name']}  
                        - Lease Term: {top_product["properties"]['lease_term']}  
                        """

    return results
