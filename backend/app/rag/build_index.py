import faiss
import pickle
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from pathlib import Path

# ===============================
# CONFIG
# ===============================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data" / "source_docs"
INDEX_DIR = BASE_DIR / "data" / "faiss_index"

INDEX_DIR.mkdir(parents=True, exist_ok=True)

INDEX_FILE = INDEX_DIR / "index.faiss"
DOCS_FILE = INDEX_DIR / "docs.pkl"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BATCH_SIZE = 32

# ===============================
# MODEL
# ===============================

print(f"Loading embedding model: {EMBEDDING_MODEL}")

model = SentenceTransformer(EMBEDDING_MODEL)

# ===============================
# CHUNK FUNCTION
# ===============================


def chunk_text(text, chunk_size=500, overlap=50):

    words = text.split()
    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# ===============================
# LOAD PDF FILES
# ===============================

pdf_files = list(DATA_DIR.glob("*.pdf"))

if not pdf_files:
    raise RuntimeError("Geen PDF bestanden gevonden in source_docs")

documents = []
texts = []

total_pages = 0

# ===============================
# PARSE PDFS
# ===============================

for pdf_file in pdf_files:

    print(f"Processing: {pdf_file.name}")

    reader = PdfReader(str(pdf_file))

    for page_number, page in enumerate(reader.pages, start=1):

        total_pages += 1

        text = page.extract_text()

        if not text:
            continue

        text = text.strip()

        if len(text) < 100:
            continue

        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)

        for i, chunk in enumerate(chunks):

            documents.append({
                "text": chunk,
                "source": pdf_file.name,
                "page": page_number,
                "chunk_id": i
            })

            texts.append(chunk)

print(f"Total PDFs: {len(pdf_files)}")
print(f"Total pages processed: {total_pages}")
print(f"Total chunks: {len(texts)}")

if not texts:
    raise RuntimeError("Geen bruikbare tekst gevonden in PDFs")

# ===============================
# GENERATE EMBEDDINGS
# ===============================

print("Generating embeddings...")

embeddings = model.encode(
    texts,
    batch_size=BATCH_SIZE,
    show_progress_bar=True
)

embeddings = np.array(embeddings).astype("float32")

# cosine similarity
faiss.normalize_L2(embeddings)

dimension = embeddings.shape[1]

print(f"Embedding dimension: {dimension}")

# ===============================
# BUILD FAISS INDEX
# ===============================

print("Building FAISS index...")

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

print(f"Vectors indexed: {index.ntotal}")

# ===============================
# SAVE FILES
# ===============================

print("Saving index...")

faiss.write_index(index, str(INDEX_FILE))

with open(DOCS_FILE, "wb") as f:
    pickle.dump(documents, f)

print("Index succesvol gebouwd.")
print(f"Index path: {INDEX_FILE}")
print(f"Docs path: {DOCS_FILE}")