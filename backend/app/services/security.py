import re
import unicodedata
from typing import Tuple, Optional

# ==============================
# CONFIGURATIE
# ==============================
MAX_QUERY_LENGTH = 500  # Vragen van studenten zijn kort
MAX_CONTEXT_LENGTH = 4000 # Boekteksten zijn lang
SYMBOL_RATIO_THRESHOLD = 0.35 

# Patronen die we ALTIJD blokkeren in de vraag van de gebruiker
STRICT_PATTERNS = [
    r"(?i)(ignore|disregard|override)\s+(all|previous|system)\s+instructions",
    r"(?i)you\s+are\s+now\s+a\s+(developer|hacker|jailbroken|god\s+mode)",
    r"(?i)bypass\s+the\s+filter",
    r"(?i)print\s+the\s+system\s+prompt"
]

# ==============================
# 1. FUNCTIES VOOR ROUTES.PY
# ==============================

def detect_prompt_injection(query: str, user_ip: Optional[str] = None) -> Tuple[str, str]:
    """
    Controleert de vraag op kwaadaardige intenties.
    Returns: (status, reason) -> status is "SAFE", "SUSPICIOUS", of "BLOCKED"
    """
    normalized = unicodedata.normalize("NFKC", query).lower()

    # Check op lengte
    if len(normalized) > MAX_QUERY_LENGTH:
        return "BLOCKED", "Vraag is te lang."

    # Check op agressieve patronen
    for pattern in STRICT_PATTERNS:
        if re.search(pattern, normalized):
            return "BLOCKED", "Onveilige instructie gedetecteerd."

    # Als het door de eerste checks komt maar veel vreemde tekens bevat
    # zou je het als "SUSPICIOUS" kunnen markeren.
    return "SAFE", "OK"

def sanitize_prompt(query: str) -> str:
    """
    Schoont de tekst op (bijv. bij status SUSPICIOUS).
    """
    # Verwijder overtollige witruimte en normaliseer karakters
    return unicodedata.normalize("NFKC", query).strip()

# ==============================
# 2. FILTER VOOR BOEKEN/RAG (MILDE)
# ==============================

def sanitize_rag_context(context_text: str) -> str:
    """
    Schoont tekst uit PDF-boeken op zodat deze de AI niet verwart.
    """
    # 1. Normaliseer (verwijder vreemde verborgen tekens uit PDF's)
    clean_text = unicodedata.normalize("NFKC", context_text)
    
    # 2. Verwijder specifieke AI-tags
    tags_to_remove = [r"(?i)system:", r"(?i)assistant:", r"(?i)user:", r"(?i)role:"]
    for pattern in tags_to_remove:
        clean_text = re.sub(pattern, "[info]", clean_text)

    # 3. Kap af op de maximale lengte
    return clean_text[:MAX_CONTEXT_LENGTH].strip()

# ==============================
# 3. DE COMBINATIE (STRATEGISCHE PROMPT)
# ==============================

def secure_rag_prompt(user_query: str, retrieved_context: str) -> Optional[str]:
    """
    Bouwt een veilige prompt door de vraag te valideren en de context te isoleren.
    Gebruik deze functie in je ai_service.py voor maximale veiligheid.
    """
    # Stap A: Valideer de vraag
    status, reason = detect_prompt_injection(user_query)
    if status == "BLOCKED":
        return None 

    # Stap B: Schoon de boektekst op
    safe_context = sanitize_rag_context(retrieved_context)

    # Stap C: Bouw de prompt met "Delimiters" (isolatie)
    final_prompt = f"""Beantwoord de vraag van de gebruiker strikt op basis van de onderstaande brontekst. 
Indien het antwoord niet in de bron staat, zeg dit dan eerlijk.

BRONMATERIAAL_START
{safe_context}
BRONMATERIAAL_END

GEBRUIKERSVRAAG: {user_query}

ANTWOORD:"""
    
    return final_prompt
    
