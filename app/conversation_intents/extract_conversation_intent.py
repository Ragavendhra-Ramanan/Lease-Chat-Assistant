import json
from datetime import datetime, timezone
from pathlib import Path
import re
import os

# In-memory stores
vehicle_memory_stores = {
    "unstructured_vehicle": {},
    "structured_vehicle": {},
    "dislike_unstructured_vehicle": {},
    "dislike_structured_vehicle": {}
}

base_dir = os.path.dirname(os.path.abspath(__file__))
# File paths
vehicle_file_paths = {
    "unstructured_vehicle": "../data/conversation_intents/vehicles/unstructured_vehicle.json",
    "structured_vehicle": "../data/conversation_intents/vehicles/structured_vehicle.json",
    "dislike_unstructured_vehicle": "../data/conversation_intents/vehicles/dislike_unstructured_vehicle.json",
    "dislike_structured_vehicle": "../data/conversation_intents/vehicles/dislike_structured_vehicle.json"
}
# In-memory stores
product_memory_stores = {
    "unstructured_product": {},
    "structured_product": {},
    "dislike_unstructured_product": {},
    "dislike_structured_product": {}
}

# File paths
product_file_paths = {
    "unstructured_product": "../data/conversation_intents/products/unstructured_product.json",
    "structured_product": "../data/conversation_intents/products/structured_product.json",
    "dislike_unstructured_product": "../data/conversation_intents/products/dislike_unstructured_product.json",
    "dislike_structured_product": "../data/conversation_intents/products/dislike_structured_product.json"
}

def contains_number(value: str):
    """Check if value contains at least one digit."""
    return bool(re.search(r'\d', value))

from datetime import datetime, timezone
import re


def is_structured(value: str) -> bool:
    """
    Returns True if value is structured (contains a full number with optional operator).
    Examples:
      '=36'        -> True
      '<40000'     -> True
      '>=2020'     -> True
      'BMW X3'     -> False
      'Red Toyota' -> False
    """
    value = value.strip()
    pattern = r'^(?:=|!=|<=|>=|<|>)?\s*\d+(\.\d+)?$'
    return bool(re.match(pattern, value))

def append_preference(user_id: str, preference_string: str, types: str):
    """Append preferences to memory with structured/unstructured separation and likes/dislikes grouping."""
    now = datetime.now(timezone.utc).isoformat()

    # Select memory store
    if types == "Vehicle":
        memory_stores = vehicle_memory_stores
        suffix = "_vehicle"
    elif types == "Product":
        memory_stores = product_memory_stores
        suffix = "_product"
    else:
        raise ValueError(f"Unknown type: {types}")

    unstructured_like_values = []
    unstructured_dislike_values = []

    for item in preference_string.split(','):
        if ':' not in item:
            continue

        field, value = item.split(':', 1)
        field = field.strip()
        value = value.lstrip()

        # Detect dislike
        dislike = False
        if value.startswith('!='):
            dislike = True
            value = value[2:].lstrip()
        elif value.startswith('!'):
            dislike = True
            value = value[1:].lstrip()

        # Remove leading '=' if present (for numeric expressions)
        if value.startswith('='):
            value = value[1:].lstrip()

        # Determine structured/unstructured
        if is_structured(value):
            store_name = "dislike_structured" if dislike else "structured"
            entry = {"field": field, "value": value, "timestamp": now}
            store_name += suffix
            memory_stores.setdefault(store_name, {}).setdefault(user_id, []).append(entry)
        else:
            # Collect unstructured values separately for like/dislike
            if dislike:
                unstructured_dislike_values.append(value)
            else:
                unstructured_like_values.append(value)

    # Store concatenated unstructured likes
    if unstructured_like_values:
        query_str = " ".join(unstructured_like_values)
        store_name = "unstructured" + suffix
        entry = {"query": query_str, "timestamp": now}
        if user_id in memory_stores.get(store_name, {}):
            memory_stores[store_name][user_id][0]["value"] += " " + query_str
        else:
            memory_stores.setdefault(store_name, {})[user_id] = [entry]

    # Store concatenated unstructured dislikes
    if unstructured_dislike_values:
        query_str = " ".join(unstructured_dislike_values)
        store_name = "dislike_unstructured" + suffix
        entry = {"query": query_str, "timestamp": now}
        if user_id in memory_stores.get(store_name, {}):
            memory_stores[store_name][user_id][0]["value"] += " " + query_str
        else:
            memory_stores.setdefault(store_name, {})[user_id] = [entry]


def save_all_to_file(types: str):
    """
    Save in-memory data to file.
    If user_id exists in JSON, append entries; else, create new user node.
    Clears the in-memory store after saving.
    """
    if types == "Vehicle":
        memory_stores = vehicle_memory_stores
        file_paths = vehicle_file_paths
    elif types == "Product":
        memory_stores = product_memory_stores
        file_paths = product_file_paths
    else:
        raise ValueError(f"Unknown type: {types}")

    for store_name, data in memory_stores.items():
        path = os.path.join(base_dir, file_paths[store_name])
        existing_data = {}

        # Load existing data
        if Path(path).exists():
            with open(path, "r") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = {}

        # Append or create new user entries
        for user_id, entries in data.items():
            user_id_str = str(user_id)
            if user_id_str in existing_data:
                existing_data[user_id_str].extend(entries)
            else:
                existing_data[user_id_str] = entries

        # Save back to file
        with open(path, "w") as f:
            json.dump(existing_data, f, indent=2)

        # Clear memory for this store
        memory_stores[store_name] = {}

def get_user_preferences(store_name: str, user_id: str, types :str):
    if (types=="Vehicle"):
            memory_stores = vehicle_memory_stores
            store_name = f"{store_name}_vehicle"
    elif (types == "Product"):
        memory_stores = product_memory_stores
        store_name = f"{store_name}_product"
    return memory_stores.get(store_name, {}).get(user_id, [])

def load_user_preferences_dict(user_id: str, types: str):
    """
    Load all preference categories from JSON files for a given user_id
    and return as a dictionary with file/category names as keys.
    """
    if types == "Vehicle":
        file_paths = vehicle_file_paths
        suffix = "vehicle"
    elif types == "Product":
        file_paths = product_file_paths
        suffix = "product"
    else:
        raise ValueError(f"Unknown type: {types}")

    user_prefs = {}

    for store_key in ["unstructured", "structured", "dislike_unstructured", "dislike_structured"]:
        file_key = f"{store_key}_{suffix}"
        path = os.path.join(base_dir, file_paths[file_key])
        data = {}
        if Path(path).exists():
            with open(path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        user_prefs[file_key] = data.get(str(user_id), [])

    return user_prefs
