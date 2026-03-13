from sentence_transformers import CrossEncoder
import torch
import logging

logger = logging.getLogger(__name__)

_model = None


# ===============================
# LOAD RERANKER
# ===============================

def get_reranker():
    global _model

    if _model is None:

        device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Loading reranker on {device}")

        _model = CrossEncoder(
            "BAAI/bge-reranker-base",
            device=device
        )

    return _model


# ===============================
# RERANK FUNCTION
# ===============================

def rerank(query: str, docs: list, top_k: int = 5):

    if not docs:
        return []

    model = get_reranker()

    pairs = []

    for doc in docs:

        text = doc.get("text", "")

        # truncate long docs
        text = text[:1000]

        pairs.append([query, text])

    try:

        scores = model.predict(
            pairs,
            batch_size=16,
            show_progress_bar=False
        )

    except Exception as e:

        logger.error(f"Reranker failure: {e}")

        return docs[:top_k]

    for doc, score in zip(docs, scores):

        doc["rerank_score"] = float(score)

    docs.sort(
        key=lambda x: x.get("rerank_score", 0),
        reverse=True
    )

    return docs[:top_k]