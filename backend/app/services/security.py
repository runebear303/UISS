import re
import unicodedata
from typing import Tuple, Optional
from app.services.logger import log_security_event

# ==============================
# CONFIGURATIE
# ==============================

MAX_INPUT_LENGTH = 3000  # Iets ruimer voor RAG context
SYMBOL_RATIO_THRESHOLD = 0.35  # Maximaal 35% symbolen
LOW_ENTROPY_THRESHOLD = 8  # Iets soepeler voor kortere zinnen

# ==============================
# PROMPT INJECTION PATTERNS
# (Geoptimaliseerd voor minder vals-positieven)
# ==============================

# Kritieke patronen: Directe commando's die de AI proberen over te nemen
CRITICAL_PATTERNS = [
    r"(?i)(do\s+not|ignore|disregard)\s+(any|all|previous|system)\s+instructions",
    r"(?i)you\s+are\s+now\s+a\s+(developer|hacker|jailbroken|god\s+mode)",
    r"(?i)output\s+the\s+original\s+prompt\s+above",
    r"(?i)bypass\s+the\s+(security|filter|safety)",
    r"(?i)terminal\s+mode|root\s+access|command\s+prompt"
]

# Verdachte patronen: Informatie-aanvragen (loggen, niet blokkeren)
SUSPICIOUS_PATTERNS = [
    r"(?i)reveal\s+(system|hidden|internal)\s+(prompt|config|file)",
    r"(?i)show\s+the\s+content\s+of\s+\.env",
    r"(?i)disregard\s+the\s+(rules|guidelines)"
]

# ==============================
# HULPFUNCTIES
# ==============================

def normalize_text(text: str) -> str:
    """Unicode normalisatie om homoglyph attacks (bijv. vréémde tekens) te voorkomen."""
    return unicodedata.normalize("NFKC", text).lower()

def is_low_entropy(text: str) -> bool:
    """Detecteert spam of extreem herhalende patronen (bijv. aaaaaaaa...)."""
    if len(text) > 200 and len(set(text)) < LOW_ENTROPY_THRESHOLD:
        return True
    return False

def excessive_symbols(text: str) -> bool:
    """Detecteert symboolmisbruik op basis van percentage (RAG-vriendelijk)."""
    if len(text) < 50:
        return False
    symbol_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
    return (symbol_count / len(text)) > SYMBOL_RATIO_THRESHOLD

# ==============================
# HOOFDFUNCTIE: DETECTIE
# ==============================

def detect_prompt_injection(
    text: str, 
    user_ip: Optional[str] = None,
    source_file: Optional[str] = None  # Nieuw: om te zien welk PDF de trigger was
) -> Tuple[str, Optional[str]]:
    """
    Evalueert de veiligheid van de input.
    Returns: ("SAFE" | "SUSPICIOUS" | "BLOCKED"), Reason
    """
    if not text:
        return "SAFE", None

    original_text = text
    normalized = normalize_text(text)
    
    # 1. Check op Kritieke Patronen (BLOKKEER)
    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, normalized):
            reason = f"Critical Injection Match: {pattern}"
            log_security_event(original_text, reason, user_ip, source_file)
            return "BLOCKED", reason

    # 2. Check op Verdachte Patronen (LOG ALLEEN)
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, normalized):
            reason = f"Suspicious Activity: {pattern}"
            log_security_event(original_text, reason, user_ip, source_file)
            return "SUSPICIOUS", reason

    # 3. Symbool Misbruik (Percentage-based)
    if excessive_symbols(normalized):
        reason = "Excessive symbol ratio detected (possible obfuscation)"
        log_security_event(original_text, reason, user_ip, source_file)
        return "SUSPICIOUS", reason

    # 4. Entropy / Spam Check
    if is_low_entropy(normalized):
        reason = "Low entropy / Repetitive input"
        return "SUSPICIOUS", reason

    # 5. Lengte Check
    if len(normalized) > MAX_INPUT_LENGTH:
        reason = "Input exceeds safety length limit"
        log_security_event("TEXT_TOO_LONG", reason, user_ip, source_file)
        return "BLOCKED", reason

    return "SAFE", None

# ==============================
# PROMPT SANITIZATION
# ==============================

def sanitize_prompt(text: str, max_length: int = 2000) -> str:
    """
    Schoont de tekst op zonder de inhoud te breken.
    Verwijdert system-tokens en model-specifieke commando's.
    """
    clean_text = unicodedata.normalize("NFKC", text)

    # Verwijder specifieke tokens die de AI kunnen verwarren over wie er spreekt
    blacklist_patterns = [
        r"(?i)system:", 
        r"(?i)assistant:", 
        r"(?i)user:", 
        r"(?i)role:",
        r"<\|.*?\|>"  # Verwijdert model tokens zoals <|endoftext|>
    ]

    for pattern in blacklist_patterns:
        clean_text = re.sub(pattern, "[removed]", clean_text)

    return clean_text[:max_length].strip()
    
