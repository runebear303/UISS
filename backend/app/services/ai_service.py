import time
from sqlalchemy.orm import Session

from app.services.hallucination import detect_hallucination
from app.services.guardrails import answer_supported_by_sources
from app.services.security import sanitize_prompt, detect_prompt_injection

from app.services.llm.llm_orchestrator import ask_llm
from app.services.llm.llm_cloud import CloudLLM

from app.services.logger import log_chat, get_today_cloud_cost
from app.rag.rag import search_docs

# ===============================
# CONFIG
# ===============================
MAX_CONTEXT_CHUNKS = 5
CONFIDENCE_THRESHOLD = 0.65
DAILY_CLOUD_LIMIT = 5.00

cloud_llm = CloudLLM()

# ===============================
# MAIN AI SERVICE
# ===============================
def ask_ai_with_sources(db: Session, vraag: str):
    # --- Initialisatie ---
    provider = None
    usage = None
    cost = 0.0
    confidence = 0.0
    docs = []
    antwoord = ""
    start_time = time.time()

    # 1️⃣ Prompt Injection Detectie
    status, reason = detect_prompt_injection(vraag)
    if status == "BLOCKED":
        provider = "blocked_injection"
        antwoord = "Je vraag bevat mogelijk onveilige instructies en is geblokkeerd."
        log_chat(db=db, prompt=vraag, response=antwoord, provider=provider)
        return {
            "answer": antwoord, 
            "sources": [], 
            "confidence": 0.0,
            "usage": None, 
            "cost": 0.0, 
            "provider": provider, 
            "latency_ms": 0
        }

    # 2️⃣ Sanitization & 3️⃣ RAG Retrieval
    vraag = sanitize_prompt(vraag)
    docs = search_docs(vraag, k=MAX_CONTEXT_CHUNKS)

    if not docs:
        provider = "no_context"
        antwoord = "Dit staat niet in de studentenhandleiding of het orde reglement van UNASAT."
        log_chat(db=db, prompt=vraag, response=antwoord, provider=provider)
        return {
            "answer": antwoord, 
            "sources": [], 
            "confidence": 0.0,
            "usage": None, 
            "cost": 0.0, 
            "provider": provider, 
            "latency_ms": 0
        }

    # 4️⃣ Context Limiter & 5️⃣ Confidence Score
    docs = docs[:MAX_CONTEXT_CHUNKS]
    context_list = []
    scores = []

    for d in docs:
        # Zorg dat we altijd tekst en een score hebben (veilig voor dicts en strings)
        text = d.get("text", str(d)) if isinstance(d, dict) else str(d)
        score = d.get("score", 0) if isinstance(d, dict) else 0
        context_list.append(text)
        scores.append(score)

    context = "\n\n".join(context_list)
    confidence = round(sum(scores) / len(docs), 2) if docs else 0.0

    # 6️⃣ Prompt Constructie
    prompt = f"Je bent een UNASAT assistent. Gebruik de context om de vraag te beantwoorden.\n\nContext:\n{context}\n\nVraag: {vraag}"

    try:
        # 7️⃣ Routing (Lokaal TinyLlama vs Cloud)
        if confidence < CONFIDENCE_THRESHOLD:
            # Check Cloud Budget
            if get_today_cloud_cost(db) >= DAILY_CLOUD_LIMIT:
                latency_ms = int((time.time() - start_time) * 1000)
                return {
                    "answer": "Dagelijkse budgetlimiet bereikt. Probeer het morgen weer.", 
                    "sources": [], 
                    "confidence": confidence, 
                    "usage": None, 
                    "cost": 0.0, 
                    "provider": "cloud_budget_exceeded", 
                    "latency_ms": latency_ms
                }
            
            # Gebruik Cloud LLM
            result = cloud_llm.generate(prompt)
            provider = "cloud_low_confidence"
        else:
            # Gebruik Lokaal TinyLlama via Orchestrator
            result = ask_llm(prompt)
            provider = result.get("provider", "local_orchestrated")

        antwoord = result.get("text", "")
        usage = result.get("usage")
        cost = result.get("cost", 0.0)

        # 8️⃣ Hallucination Guardrail
        # We checken de eerste 3 bronnen voor de meest relevante feiten
        docs_for_check = docs[:3]
        
        hallucination_found = detect_hallucination(antwoord, docs_for_check)
        support_missing = not answer_supported_by_sources(antwoord, docs_for_check)

        # Deze prints verschijnen in je Docker / VS Code terminal
        print(f"DEBUG: Hallucination check result: {hallucination_found}")
        print(f"DEBUG: Support missing result: {support_missing}")

        if hallucination_found or support_missing:
            provider = "hallucination_blocked"
            antwoord = "Het antwoord kon niet betrouwbaar worden bevestigd door de beschikbare bronnen."

    except Exception as e:
        print(f"CRITICAL LLM ERROR: {e}")
        provider = "llm_error"
        antwoord = "Er is een interne fout opgetreden bij het verwerken van je vraag."

    # --- Finale Formattering & Opslag ---
    latency_ms = int((time.time() - start_time) * 1000)
    
    formatted_sources = []
    for d in docs:
        if isinstance(d, dict):
            formatted_sources.append(d)
        else:
            formatted_sources.append({"text": str(d), "source_file": "Onbekende bron"})

    try:
        log_chat(db=db, prompt=vraag, response=antwoord, provider=provider, usage=usage, cost=cost)
    except Exception as db_e:
        print(f"Database logging failed: {db_e}")

    return {
        "answer": antwoord,
        "sources": formatted_sources,
        "confidence": confidence,
        "usage": usage,
        "cost": cost,
        "provider": provider,
        "latency_ms": latency_ms
    }