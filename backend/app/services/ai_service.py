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
    # Alles binnen de functie heeft minimaal 1 TAB (4 spaties)
    provider = None
    usage = None
    cost = 0.0
    confidence = 0.0
    docs = []
    antwoord = ""

    # ===============================
    # 1️⃣ Prompt Injection Detectie
    # ===============================
    # We vangen de status op uit de tuple die security.py teruggeeft
    status, reason = detect_prompt_injection(vraag)

    if status == "BLOCKED":
        provider = "blocked_injection"
        antwoord = "Je vraag bevat mogelijk onveilige instructies en is geblokkeerd."

        # Deze regels horen bij de IF en hebben 2 TABS (8 spaties)
        try:
            log_chat(
                db=db,
                prompt=vraag,
                response=antwoord,
                provider=provider
            )
        except Exception as e:
            print("Security log failed:", e)

        # De return moet IN de IF staan om de rest van de functie te stoppen
        return {
            "answer": antwoord,
            "sources": [],
            "confidence": 0.0,
            "usage": None,
            "cost": 0.0,
            "provider": provider,
            "security_blocked": True,
            "latency_ms": 0
        }


    # ===============================
    # 2️⃣ Sanitization
    # ===============================

    vraag = sanitize_prompt(vraag)

    # ===============================
    # 3️⃣ RAG Retrieval
    # ===============================

    docs = search_docs(vraag, k=MAX_CONTEXT_CHUNKS)

    if not docs:

        provider = "no_context"
        antwoord = "Dit staat niet in de studentenhandleiding of het orde reglement."

        log_chat(
            db=db,
            prompt=vraag,
            response=antwoord,
            provider=provider
        )

        return {
            "answer": antwoord,
            "sources": [],
            "confidence": 0.0,
            "usage": None,
            "cost": 0.0,
            "provider": provider
        }

    # ===============================
    # 4️⃣ Context Limiter
    # ===============================

    docs = docs[:MAX_CONTEXT_CHUNKS]

    context_list = []

    for d in docs:
     if isinstance(d, dict) and "text" in d:
        context_list.append(d["text"])
    else:
        context_list.append(str(d)) # 

    context = "\n\n".join(context_list)

    # ===============================
    # 5️⃣ Confidence Score
    # ===============================

    if not docs:
        confidence = 0.0
    else:
        # We controleren per item of het een dictionary is
        scores = []
        for d in docs:
            if isinstance(d, dict):
                scores.append(d.get("score", 0))
            else:
                # Als het een string is, hebben we geen score, dus 0
                scores.append(0)
        
        confidence = sum(scores) / len(docs)
    
    confidence = round(confidence, 2)

    # ===============================
    # 6️⃣ Prompt Constructie
    # ===============================

    prompt = f"""
Je bent een academische FAQ-chatbot voor studenten van UNASAT.

STRIKTE REGELS:
- Gebruik ALLEEN de onderstaande context.
- Verzín geen informatie.
- Als het antwoord niet letterlijk in de context staat, zeg:
  "Dit staat niet in de studentenhandleiding of het orde reglement."

Context:
{context}

Vraag: {vraag}

Antwoord in correct en duidelijk Nederlands.
"""

    start_time = time.time()

    try:

        # ===============================
        # 7️⃣ Routing + Budget Controle
        # ===============================

        if confidence < CONFIDENCE_THRESHOLD:

            if get_today_cloud_cost(db) >= DAILY_CLOUD_LIMIT:

                provider = "cloud_budget_exceeded"
                antwoord = "Dagelijkse cloud AI budgetlimiet is bereikt."

                log_chat(
                    db=db,
                    prompt=vraag,
                    response=antwoord,
                    provider=provider
                )

                return {
                    "answer": antwoord,
                    "sources": docs,
                    "confidence": confidence,
                    "usage": None,
                    "cost": 0.0,
                    "provider": provider
                }

            result = cloud_llm.generate(prompt)
            provider = "cloud_low_confidence"

        else:

            result = ask_llm(prompt)
            provider = result.get("provider", "local_orchestrated")

        antwoord = result.get("text", "")
        usage = result.get("usage")
        cost = result.get("cost", 0.0)

        # ===============================
        # 8️⃣ Hallucination Guardrail
        # ===============================

        docs_for_guardrail = docs[:3]

        if detect_hallucination(antwoord, docs_for_guardrail) or \
           not answer_supported_by_sources(antwoord, docs_for_guardrail):

            provider = "hallucination_blocked"

            antwoord = "Het antwoord kon niet betrouwbaar worden bevestigd door de beschikbare bronnen."

            log_chat(
                db=db,
                prompt=vraag,
                response=antwoord,
                provider=provider
            )

            return {
                "answer": antwoord,
                "sources": docs,
                "confidence": confidence,
                "usage": None,
                "cost": 0.0,
                "provider": provider
            }

    except Exception:

        provider = "llm_error"
        antwoord = "Er is een interne fout opgetreden bij het genereren van een antwoord."

        log_chat(
            db=db,
            prompt=vraag,
            response=antwoord,
            provider=provider
        )

        return {
            "answer": antwoord,
            "sources": docs,
            "confidence": confidence,
            "usage": None,
            "cost": 0.0,
            "provider": provider
        }

    latency_ms = int((time.time() - start_time) * 1000)

    # ===============================
    # Logging
    # ===============================

    log_chat(
        db=db,
        prompt=vraag,
        response=antwoord,
        provider=provider,
        usage=usage,
        cost=cost
    )

    return {
        "answer": antwoord,
        "sources": docs,
        "confidence": confidence,
        "usage": usage,
        "cost": cost,
        "provider": provider,
        "latency_ms": latency_ms
    }