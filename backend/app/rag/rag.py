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

# ===============================
# 1. CONFIGURATIE & INITIALISATIE
# ===============================
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
ollama_client = Client(host=OLLAMA_HOST)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_model = None

# Paden naar de bestanden (via Docker Volumes gekoppeld)
INDEX_FILE = FAISS_PATH
DOCS_FILE = FAISS_PATH.parent / "docs.pkl"
DIMENSION = 384
# Global variabelen voor de actieve index in het geheugen
index = None
documents = []

# ===============================
# 2. HULPFUNCTIES
# ===============================
def get_model():
    """Laadt het embedding model eenmalig in het geheugen (Singleton)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def sanitize_query(q: str):
    """Eenvoudige beveiliging tegen prompt injection in de zoekopdracht."""
    blacklist = ["system:", "ignore instructions", "jailbreak", "role:"]
    q = q.lower()
    for b in blacklist:
        q = q.replace(b, "")
    return q[:500]

# ===============================
# 3. LADEN VAN DE INDEX (Bij opstarten)
# ===============================
def load_index():
    global index, documents
    if INDEX_FILE.exists():
        try:
            index = faiss.read_index(str(INDEX_FILE))
            with open(DOCS_FILE, "rb") as f:
                documents = pickle.load(f)
            print(f"✅ FAISS index geladen: {index.ntotal} segmenten beschikbaar.")
        except Exception as e:
            print(f"❌ Fout bij laden index: {e}. Start met lege index.")
            index = faiss.IndexFlatIP(DIMENSION )
            documents = []
    else:
        print("⚠️ Geen bestaande index gevonden. Nieuwe index wordt aangemaakt.")
        index = faiss.IndexFlatIP(DIMENSION) # 384 is de dimensie voor MiniLM
        documents = []

# Voer de lader direct uit bij importeren
load_index()

# ===============================
# 4. CORE RAG FUNCTIES
# ===============================

def add_to_index(chunks: list, source_name: str):
    """
    Voegt nieuwe tekstsegmenten toe aan de FAISS index en slaat deze permanent op.
    """
    global index, documents
    
    model = get_model()
    
    # Maak embeddings van de nieuwe tekst
    embeddings = model.encode(chunks)
    embeddings = np.array(embeddings).astype('float32')

    # Voeg toe aan de actieve index en metadata lijst
    index.add(embeddings)
    for chunk in chunks:
        documents.append({
            "text": chunk, 
            "source": source_name,
            "timestamp": time.time()
        })

    # Opslaan naar de persistente volume mappen
    try:
        faiss.write_index(index, str(INDEX_FILE))
        with open(DOCS_FILE, "wb") as f:
            pickle.dump(documents, f)
        print(f"✅ {len(chunks)} segmenten toegevoegd van bron: {source_name}")
    except Exception as e:
        print(f"❌ Fout bij opslaan index naar schijf: {e}")

def search_docs(query: str, k=5):
    """Zoekt de meest relevante tekstfragmenten voor een vraag."""
    query = sanitize_query(query)
    model = get_model()
    
    # Vertaal vraag naar vector
    emb = model.encode([query])
    D, I = index.search(emb, k)

    results = []
    for score, idx in zip(D[0], I[0]):
        # Filter op index grenzen en relevantie score (L2 distance)
        if idx < 0 or idx >= len(documents) or score > 1.5:
            continue
        
        doc = documents[idx]
        results.append(doc.get("text", ""))
    
    return results

# ===============================
# 5. AI GENERATIE (OLLAMA)
# ===============================

def ask_llm_stream(prompt: str):
    """Streams tokens direct van de Ollama Docker container naar de frontend."""
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
        yield " [Fout: Verbinding met AI verloren] "

def get_answer(user_query: str):
    """De volledige RAG flow: Zoeken -> Prompt bouwen -> AI aanroepen."""
    start_time = time.time()
    try:
        # 1. Context ophalen
        context_chunks = search_docs(user_query, k=3)
        context_text = "\n".join(context_chunks) if context_chunks else "Geen relevante informatie gevonden."

        # 2. Prompt samenstellen
        system_msg = (
            "Je bent de UISS (UNASAT) Assistent. Beantwoord de vraag strikt op basis van de context.\n\n"
            f"CONTEXT:\n{context_text}"
        )

        # 3. Ollama aanroepen
        response = ollama_client.generate(
            model='tinyllama:latest',
            system=system_msg,
            prompt=user_query,
            options={"temperature": 0.0}
        )

        # 4. Metrics loggen
        duration = time.time() - start_time
        AIMetrics.log_query(docs_count=len(context_chunks), response_time=duration)

        return response['response']

    except Exception as e:
        AIMetrics.log_error()
        print(f"RAG Error: {e}")
        return "Ik kan momenteel geen verbinding maken met de AI engine."