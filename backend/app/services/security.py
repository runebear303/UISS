import re
import unicodedata
from typing import Tuple, Optional
from app.services.logger import log_security_event


# ==============================
# CONFIGURATIE
# ==============================

MAX_INPUT_LENGTH = 2000
SUSPICIOUS_SYMBOL_THRESHOLD = 80
LOW_ENTROPY_THRESHOLD = 10


# ==============================
# CRITICALE PROMPT INJECTION
# (blokkeer deze)
# ==============================

CRITICAL_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"ignore\s+all\s+instructions",
    r"override\s+.*system",
    r"bypass\s+.*security",
    r"jailbreak",
    r"developer\s+mode"
]


# ==============================
# VERDACHTE PATRONEN
# (log maar blokkeer niet)
# ==============================

SUSPICIOUS_PATTERNS = [
    r"reveal\s+.*hidden",
    r"show\s+.*confidential",
    r"disregard\s+.*rules"
]


# ==============================
# NORMALISATIE
# ==============================

def normalize_text(text: str) -> str:
    """
    Unicode normalisatie om homoglyph attacks te voorkomen.
    """
    text = unicodedata.normalize("NFKC", text)
    return text.lower()


# ==============================
# ENTROPY CHECK
# ==============================

def is_low_entropy(text: str) -> bool:
    """
    Detecteert spam / herhalende patronen.
    """
    if len(text) > 200 and len(set(text)) < LOW_ENTROPY_THRESHOLD:
        return True
    return False


# ==============================
# SYMBOL ABUSE
# ==============================

def excessive_symbols(text: str) -> bool:
    """
    Detecteert overdreven symbolgebruik.
    """
    symbol_count = sum(
        1 for c in text if not c.isalnum() and not c.isspace()
    )
    return symbol_count > SUSPICIOUS_SYMBOL_THRESHOLD


# ==============================
# PROMPT INJECTION DETECTIE
# ==============================

def detect_prompt_injection(
    text: str,
    user_ip: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """
    Retourneert security niveau:

    SAFE
    SUSPICIOUS
    BLOCKED
    """

    original_text = text
    normalized = normalize_text(text)

    # ------------------------------
    # 1️⃣ CRITICAL PATTERNS
    # ------------------------------

    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):

            reason = f"Critical prompt injection: {pattern}"

            log_security_event(
                original_text,
                reason,
                user_ip
            )

            return "BLOCKED", reason

    # ------------------------------
    # 2️⃣ SUSPICIOUS PATTERNS
    # ------------------------------

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):

            reason = f"Suspicious pattern: {pattern}"

            log_security_event(
                original_text,
                reason,
                user_ip
            )

            return "SUSPICIOUS", reason

    # ------------------------------
    # 3️⃣ ENTROPY CHECK
    # ------------------------------

    if is_low_entropy(normalized):

        reason = "Low entropy suspicious input"

        log_security_event(
            original_text,
            reason,
            user_ip
        )

        return "SUSPICIOUS", reason

    # ------------------------------
    # 4️⃣ SYMBOL ABUSE
    # ------------------------------

    if excessive_symbols(normalized):

        reason = "Excessive symbol usage"

        log_security_event(
            original_text,
            reason,
            user_ip
        )

        return "SUSPICIOUS", reason

    # ------------------------------
    # 5️⃣ LENGTH CHECK
    # ------------------------------

    if len(normalized) > MAX_INPUT_LENGTH:

        reason = "Input exceeds maximum length"

        log_security_event(
            original_text,
            reason,
            user_ip
        )

        return "BLOCKED", reason

    return "SAFE", None


# ==============================
# PROMPT SANITIZATION
# ==============================

def sanitize_prompt(
    text: str,
    max_length: int = 1500
) -> str:
    """
    Soft sanitization.

    Verwijdert systeem tokens zonder
    gebruikersvraag kapot te maken.
    """

    clean_text = unicodedata.normalize("NFKC", text)

    blacklist = [
        "system:",
        "assistant:",
        "role:",
        "developer:",
        "<system>",
        "</system>"
    ]

    for token in blacklist:
        clean_text = clean_text.replace(token, "")

    return clean_text[:max_length]
    
