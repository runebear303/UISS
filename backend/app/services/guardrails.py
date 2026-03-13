import re


MIN_FACT_MATCH = 0.35


def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text


def answer_supported_by_sources(answer: str, sources: list) -> bool:

    if not sources:
        return False

    answer_words = set(normalize(answer).split())

    source_text = " ".join([s["text"] for s in sources])
    source_words = set(normalize(source_text).split())

    if not answer_words:
        return False

    overlap = answer_words.intersection(source_words)

    score = len(overlap) / len(answer_words)

    return score >= MIN_FACT_MATCH