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
# 1. DE VEILIGHEIDSKLEP VOOR DE GEBRUIKER (STRENG)
# ==============================

def validate_user_query(query: str, user_ip: Optional[str] = None) -> Tuple[bool, str]:
    """
    Controleert de vraag van de student op kwaadaardige intenties.
    """
    normalized = unicodedata.normalize("NFKC", query).lower()

    # Check op lengte
    if len(normalized) > MAX_QUERY_LENGTH:
        return False, "Vraag is te lang."

    # Check op agressieve patronen
    for pattern in STRICT_PATTERNS:
        if re.search(pattern, normalized):
            return False, f"Onveilige instructie gedetecteerd."

    return True, "SAFE"

# ==============================
# 2. DE FILTER VOOR BOEKEN/RAG (MILDE)
# ==============================

def sanitize_rag_context(context_text: str) -> str:
    """
    Schoont tekst uit PDF-boeken op zodat deze de AI niet verwart,
    zonder de inhoud te blokkeren.
    """
    # 1. Normaliseer (verwijder vreemde verborgen tekens uit PDF's)
    clean_text = unicodedata.normalize("NFKC", context_text)
    
    # 2. Verwijder specifieke AI-tags die in boeken kunnen staan (bijv. "System:", "User:")
    # We vervangen ze door een onschadelijk woord zodat de zin blijft lopen.
    tags_to_remove = [r"(?i)system:", r"(?i)assistant:", r"(?i)user:", r"(?i)role:"]
    for pattern in tags_to_remove:
        clean_text = re.sub(pattern, "[info]", clean_text)

    # 3. Kap af op de maximale lengte om resource-overbelasting te voorkomen
    return clean_text[:MAX_CONTEXT_LENGTH].strip()

# ==============================
# 3. DE COMBINATIE (HOOFDFUNCTIE)
# ==============================

def secure_rag_prompt(user_query: str, retrieved_context: str) -> Optional[str]:
    """
    Bouwt een veilige prompt door de vraag te valideren en de context te isoleren.
    """
    # Stap A: Valideer de vraag
    is_safe, message = validate_user_query(user_query)
    if not is_safe:
        return None # Hier zou je een foutmelding naar de frontend sturen

    # Stap B: Schoon de boektekst op
    safe_context = sanitize_rag_context(retrieved_context)

    # Stap C: Bouw de prompt met "Delimiters" (isolatie)
    # Dit dwingt de AI om de context als DATA te zien en niet als BEVEL.
    final_prompt = f"""Beantwoord de vraag van de gebruiker strikt op basis van de onderstaande brontekst. 
Indien het antwoord niet in de bron staat, zeg dit dan eerlijk.

BRONMATERIAAL_START
{safe_context}
BRONMATERIAAL_END

GEBRUIKERSVRAAG: {user_query}

ANTWOORD:"""
    
    return final_prompt
    
