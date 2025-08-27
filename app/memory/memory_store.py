from typing import List, Dict
from langchain.embeddings import OpenAIEmbeddings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
# from utils.secrets import openai_api_key

# # Initialize LangChain OpenAI embeddings
# embeddings_model = OpenAIEmbeddings(openai_api_key=openai_api_key)

short_term_memory: Dict[str, List[Dict]] = {}
MAX_MEMORY = 5  # store last N entries

def add_short_term_memory_from_dict(user_id: str, query: str, response: str):
    """
    Store memory with separate fields and compute embedding for semantic similarity.
    """
    if user_id not in short_term_memory:
        short_term_memory[user_id] = []

    # Compute embedding for current query
    #query_vector = embeddings_model.embed_query(query)
    
    # Flatten entity dict into top-level fields (with 'last_' prefix)
    entry = {"query": query, "response": response}
    # for key, value in entities.items():
    #     entry[f"last_{key}"] = value  # each field stored separately

    short_term_memory[user_id].append(entry)

    # Maintain memory size
    if len(short_term_memory[user_id]) > MAX_MEMORY:
        short_term_memory[user_id].pop(0)

def get_recent_memory(user_id: str) -> List[Dict]:
    return short_term_memory.get(user_id, [])

# def is_relevant_to_memory(user_id: str, current_query: str, threshold: float = 0.6) -> bool:
#     """
#     Determine if memory is relevant to current query using embeddings similarity.
#     """
#     memory_entries = get_recent_memory(user_id)
#     if not memory_entries:
#         return False

#     current_vector = np.array(embeddings_model.embed_query(current_query))
#     memory_vectors = [m['embedding'] for m in memory_entries]

#     sims = [cosine_similarity(current_vector.reshape(1, -1), v.reshape(1, -1))[0][0] for v in memory_vectors]
#     return max(sims) >= threshold

# def extract_context_from_memory(user_id: str) -> Dict:
#     """
#     Extract the latest memory entry with separate entity fields.
#     Returns a dict like {'last_customer_id': 1001, 'last_vehicle_make': 'Ford', ...}
#     """
#     memory_entries = get_recent_memory(user_id)
#     if not memory_entries:
#         return {}

#     last_entry = memory_entries[-1]
#     # Return only entity fields (exclude query, response, embedding)
#     context = {k: v for k, v in last_entry.items() if k not in ['query', 'response', 'embedding'] and v is not None}
#     return context
