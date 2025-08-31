from typing import List, Dict
from langchain.embeddings import OpenAIEmbeddings
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

short_term_memory: Dict[str, Dict[str,List[Dict]]] = {}
MAX_MEMORY = 5  # store last N entries

def add_short_term_memory_from_dict(user_id: str,conversation_id:str, query: str, response: str):
    """
    Store memory with separate fields and compute embedding for semantic similarity.
    """
    if user_id not in short_term_memory:
        short_term_memory[user_id] = dict()
    if conversation_id not in short_term_memory[user_id]:
        short_term_memory[user_id][conversation_id]=[]

    entry = {"query": query, "response": response}

    short_term_memory[user_id][conversation_id].append(entry)

    # Maintain memory size
    if len(short_term_memory[user_id][conversation_id]) > MAX_MEMORY:
        short_term_memory[user_id][conversation_id].pop(0)

def get_recent_memory(user_id: str,conversation_id:str) -> List[Dict]:
    user_memory = short_term_memory.get(user_id, False)
    if user_memory:
        return short_term_memory[user_id].get(conversation_id,[])
    else:
        return []

