import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
import os

CACHE_THRESHOLD = 0.92
CACHE_FILE = "data/cache/cache.pkl"
INDEX_FILE = "data/cache/cache.faiss"

os.makedirs("data/cache", exist_ok=True)

model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

cache_data = []
dimension = 384

if os.path.exists(INDEX_FILE):
    index = faiss.read_index(INDEX_FILE)
else:
    index = faiss.IndexFlatIP(dimension)

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "rb") as f:
        cache_data = pickle.load(f)


def get_cached_answer(query):

    if len(cache_data) == 0:
        return None

    emb = model.encode([query]).astype("float32")
    faiss.normalize_L2(emb)

    D, I = index.search(emb, 1)

    score = float(D[0][0])

    if score > CACHE_THRESHOLD:
        idx = I[0][0]
        return cache_data[idx]["answer"]

    return None


def store_cache(query, answer):

    emb = model.encode([query]).astype("float32")
    faiss.normalize_L2(emb)

    index.add(emb)

    cache_data.append({
        "query": query,
        "answer": answer
    })

    faiss.write_index(index, INDEX_FILE)

    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache_data, f)