import faiss
import pickle
import os
import time
import numpy as np
from pathlib import Path
from ollama import Client 
from sentence_transformers import SentenceTransformer
from app.config import FAISS_PATH
from app.services.ai_metrics import AIMetrics

# 1. CONFIG & INITIALISATIE
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
ollama_client = Client(host=OLLAMA_HOST)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_model = None

INDEX_FILE = FAISS_PATH
DOCS_FILE = FAISS_PATH.parent / "docs.pkl"

# Global variabelen voor de actieve index
index = None
documents = []

# 2. HULPFUNCTIES (Eerst definieren!)
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

# 3. DE NIEUWE ADD_TO_INDEX FUNCTIE
def add_to_index(chunks: list, source_name: str):
    """Voegt nieuwe tekst toe aan de FAISS index en slaat op."""
    global index, documents
    
    model = get_model()
    embeddings = model.encode(chunks)
    embeddings = np.array(embeddings).astype('float32')

    # Toevoegen aan geheugen
    index.add(embeddings)
    for chunk in chunks:
        documents.append({"text": chunk, "source": source_name})

    # Opslaan naar schijf (voor persistentie in Docker volumes)
    faiss.write_index(index, str(INDEX_FILE))
    with open(DOCS_FILE, "wb") as f:
        pickle.dump(documents, f)
    print(f"✅ {len(chunks)} segmenten toegevoegd aan de AI kennisbase.")

# 4. LADEN VAN BESTAANDE DATA
if not INDEX_FILE.exists():
    # Als er nog geen index is, maken we een lege aan (dimensie 384 voor MiniLM)
    index = faiss.IndexFlatL2(384)
    documents = []
else:
    try:
        index = faiss.read_index(str(INDEX_FILE))
        with open(DOCS_FILE, "rb") as f:
            documents = pickle.load(f)
    except Exception as e:
        print(f"Laadfout: {e}. Start met lege index.")
        index = faiss.IndexFlatL2(384)
        documents = []

# 5. JOUW BESTAANDE ZOEK & STREAM LOGICA
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
        if idx < 0 or idx >= len(documents) or score > 1.5:
            continue
        results.append(documents[idx].get("text", ""))
    return results

def ask_llm_stream(prompt: str):
    try:
        stream = ollama_client.generate(
            model='tinyllama',
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

# ... de rest van je get_answer functie ...