import re

# Iets lager zetten voor lokale modellen die natuurlijke zinnen maken
MIN_FACT_MATCH = 0.10 

# Lijst met woorden die we NIET meetellen voor de ondersteuning
STOP_WORDS = {"de", "het", "een", "is", "zijn", "en", "van", "in", "op", "met", "voor", "aan"}

def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text

def answer_supported_by_sources(answer: str, sources: list) -> bool:
    if not sources:
        return False

    # 1. Normaliseer antwoord en filter stopwoorden
    answer_words = [w for w in normalize(answer).split() if w not in STOP_WORDS]
    answer_set = set(answer_words)

    if not answer_set:
        return True # Als er geen inhoudelijke woorden zijn (bijv. "Ja"), laten we het door

    # 2. Haal tekst uit sources (veilig voor dicts en strings)
    source_texts = []
    for s in sources:
        if isinstance(s, dict):
            source_texts.append(s.get("text", ""))
        else:
            source_texts.append(str(s))
    
    source_full_text = " ".join(source_texts)
    source_words = set(normalize(source_full_text).split())

    # 3. Bereken overlap
    overlap = answer_set.intersection(source_words)
    score = len(overlap) / len(answer_set)

    print(f"DEBUG Guardrail: Score is {score:.2f} (Required: {MIN_FACT_MATCH})")

    return score >= MIN_FACT_MATCH