from sentence_transformers import SentenceTransformer
import numpy as np
import os

model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

HALLUCINATION_THRESHOLD = 0.55


def hallucination_score(answer, context_chunks):

    answer_emb = model.encode([answer])

    scores = []

    for chunk in context_chunks:

        emb = model.encode([chunk])
        sim = np.dot(answer_emb, emb.T)[0][0]
        scores.append(sim)

    if not scores:
        return 0.0

    return max(scores)


def detect_hallucination(answer, context_chunks):

    score = hallucination_score(answer, context_chunks)

    return score < HALLUCINATION_THRESHOLD