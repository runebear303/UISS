import faiss
import pickle
import os
import time
from pathlib import Path
from ollama import Client  # Make sure you've run: pip install ollama
from sentence_transformers import SentenceTransformer
from app.config import FAISS_PATH
from app.services.ai_metrics import AIMetrics

# ===============================
# OLLAMA DOCKER CONFIG
# ===============================
# Use 'http://localhost:11434' if FastAPI is local and Ollama is in Docker
# Use 'http://ollama:11434' if both are in the same Docker network
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_client = Client(host=OLLAMA_HOST)

# ===============================
# MODEL & FILE CONFIG
# ===============================
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_model = None

INDEX_FILE = FAISS_PATH
DOCS_FILE = FAISS_PATH.parent / "docs.pkl"

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

# ===============================
# LOAD INDEX + DOCS
# ===============================
if not INDEX_FILE.exists():
    raise RuntimeError(f"FAISS index not found at {INDEX_FILE}")

try:
    index = faiss.read_index(str(INDEX_FILE))
    with open(DOCS_FILE, "rb") as f:
        documents = pickle.load(f)
except Exception as e:
    raise RuntimeError(f"Failed to load FAISS/Docs: {e}")

# ===============================
# UTILITIES
# ===============================
def sanitize_query(q: str):
    blacklist = ["system:", "ignore instructions", "jailbreak", "role:"]
    q = q.lower()
    for b in blacklist:
        q = q.replace(b, "")
    return q[:500]

def search_docs(query: str, k=5):
    query = sanitize_query(query)
    model = get_model()
    emb = model.encode([query])
    D, I = index.search(emb, k)

    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(documents):
            continue
        
        # NOTE: FAISS L2 distance: Lower is better (0.0 = perfect). 
        # If score > 1.5, it's usually irrelevant.
        if score > 1.5: 
            continue

        doc = documents[idx]
        results.append(doc.get("text", ""))
    return results
# ===============================
# STREAMING LOGIC
# ===============================

def ask_llm_stream(prompt: str):
    """
    Talks to Docker Ollama and yields tokens one by one.
    """
    try:
        # We use the client initialized at the top of this file
        stream = ollama_client.generate(
            model='llama3',
            prompt=prompt,
            stream=True,
            options={"temperature": 0.2}
        )
        
        for chunk in stream:
            if 'response' in chunk:
                yield chunk['response']
            
    except Exception as e:
        print(f"Ollama Stream Error: {e}")
        yield " [Error: Connection to AI lost] "


# ===============================
# THE CORE RAG FUNCTION
# ===============================
def get_answer(user_query: str):
    start_time = time.time()
    try:
        # 1. Retrieve Context from FAISS
        context_chunks = search_docs(user_query, k=3)
        context_text = "\n".join(context_chunks) if context_chunks else "No relevant info found."

        # 2. Construct System Prompt
        system_msg = (
            "You are the UISS (UNASAT) Assistant. Answer the user strictly using the context below. "
            "If the answer isn't there, say you don't know.\n\n"
            f"CONTEXT:\n{context_text}"
        )

        # 3. Call Ollama in Docker
        response = ollama_client.generate(
            model='llama3',
            system=system_msg,
            prompt=user_query,
            options={"temperature": 0.2} # Lower temp = more factual
        )

        # 4. Log Metrics for your Dashboard
        duration = time.time() - start_time
        AIMetrics.log_query(docs_count=len(context_chunks), response_time=duration)

        return response['response']

    except Exception as e:
        AIMetrics.log_error()
        print(f"RAG Error: {e}")
        return "I'm having trouble connecting to my AI engine. Please check Docker."