from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.models.schemas import ChatRequest, ChatResponse, LoginRequest, TokenResponse
from app.services.ai_service import ask_ai_with_sources
from app.services.auth import authenticate
from app.services.dependencies import verify_admin
from app.services.monitor import system_stats
from app.services.metrics import get_ai_metrics
from app.services.logger import log_chat, log_system_alert, log_ai_usage, get_logs, get_security_events, get_monitoring_stats
from app.services.llm.llm_orchestrator import ask_llm_stream
from app.rag.rag import search_docs
from app.database.db import get_db
from app.config import MAX_INPUT_CHARS
from app.crud.crud_conversation import create_conversation, get_conversations
from app.crud.crud_messsage import create_message, get_messages
from app.services.logger import (
    log_chat, 
    log_system_alert, 
    log_ai_usage, 
    log_security_event, 
    get_logs, 
    get_security_events, 
    get_monitoring_stats
)
from app.services.security import detect_prompt_injection, sanitize_prompt, secure_rag_prompt

router = APIRouter()

MAX_INPUT_CHARS = 1000


# ======================================
# CHAT
# ======================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request, db: Session = Depends(get_db)):
    query = request.question.strip()
    user_ip = http_request.client.host

    # 1. Validatie
    if not query:
        raise HTTPException(status_code=400, detail="Vraag is leeg")
    
    # 2. Beveiliging (Injection detectie)
    status, reason = detect_prompt_injection(query, user_ip)
    if status == "BLOCKED":
        log_security_event(db, "PROMPT_INJECTION", f"Gebruiker geblokkeerd: {reason}", user_ip)
        raise HTTPException(status_code=400, detail="Onveilige vraag gedetecteerd")
    
    if status == "SUSPICIOUS":
        query = sanitize_prompt(query)

    # 3. AI Verwerking (RAG + LLM)
    result = ask_ai_with_sources(db, query)

    # 4. Opslaan in database
    try:
        create_message(db, conversation_id=request.conversation_id, role="user", content=query)
        create_message(db, conversation_id=request.conversation_id, role="assistant", content=result["answer"])
        # Log ook de technische data
        log_chat(db, query, result["answer"], result.get("usage", {}), result.get("provider", "local"))
    except Exception as e:
        print(f"Fout bij opslaan geschiedenis: {e}")

    return result

    # =========================
    # PROMPT SECURITY CHECK
    # =========================

    user_ip = http_request.client.host

    status, reason = detect_prompt_injection(query, user_ip)

    if status == "BLOCKED":
        raise HTTPException(
            status_code=400,
            detail="Je vraag bevat mogelijk onveilige instructies"
        )

    if status == "SUSPICIOUS":
        query = sanitize_prompt(query)

    # =========================
    # Ask AI
    # =========================

    result = ask_ai_with_sources(db, query)

    # =========================
    # Save conversation history
    # =========================

    try:

        create_message(
            db,
            conversation_id=request.conversation_id,
            role="user",
            content=query
        )

        create_message(
            db,
            conversation_id=request.conversation_id,
            role="assistant",
            content=result["answer"]
        )

    except Exception as e:
        print("Message history insert failed:", e)

    return result


# ======================================
# STREAM CHAT
# ======================================

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, http_request: Request, db: Session = Depends(get_db)):
    query = request.question.strip()
    user_ip = http_request.client.host

    # Beveiliging
    status, _ = detect_prompt_injection(query, user_ip)
    if status == "BLOCKED":
        raise HTTPException(status_code=400, detail="Beveiligingsrisico")

    # RAG Zoekopdracht
    docs = search_docs(query)
    context_text = "\n\n".join([doc["text"] for doc in docs]) if docs else "Geen context gevonden."
    
    final_prompt = secure_rag_prompt(query, context_text)

    async def stream_generator():
        full_response = ""
        # Gebruik ASYNC for voor de asynchrone httpx stream
        async for token in ask_llm_stream(final_prompt):
            full_response += token
            yield token
        
        # Optioneel: Sla het volledige antwoord op in de DB nadat de stream klaar is
        # create_message(db, request.conversation_id, "assistant", full_response)

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

    # =========================
    # PROMPT SECURITY CHECK
    # =========================

    user_ip = http_request.client.host

    status, reason = detect_prompt_injection(query, user_ip)

    if status == "BLOCKED":
        raise HTTPException(
            status_code=400,
            detail="Je vraag bevat mogelijk onveilige instructies"
        )

    if status == "SUSPICIOUS":
        query = sanitize_prompt(query)

    # =========================
    # RAG SEARCH
    # =========================

    docs = search_docs(query)

    if not docs:
        async def empty_stream():
            yield "Ik kan deze informatie niet vinden in de beschikbare documentatie van UNASAT."
        return StreamingResponse(empty_stream(), media_type="text/plain")

    context_text = "\n\n".join([doc["text"] for doc in docs])

    prompt = f"""
Je bent een behulpzame informatie-assistent voor studenten.
Gebruik de onderstaande tekst om de vraag te beantwoorden.

Beschikbare informatie:
{context_text}

Vraag: {query}

Instructies:
- Geef een feitelijk antwoord op basis van de tekst.
- Als het antwoord er niet in staat, zeg dan dat je het niet weet.
- Antwoord in het Nederlands.
"""

    async def stream_generator():
        for token in ask_llm_stream(prompt):
            yield token

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


# ======================================
# LOGIN
# ======================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db  # Importeer je database sessie generator
# Zorg dat je ook de nieuwe authenticate import uit je auth service

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    # We geven nu 'db' mee aan de authenticate functie
    token = authenticate(db, request.username, request.password)

    if not token:
        # Hier komt nu die "Invalid credentials" vandaan als de hash niet klopt
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": token, "token_type": "bearer"}


# ======================================
# ADMIN
# ======================================

@router.get("/admin")
def admin_info(user=Depends(verify_admin)):
    return {"username": user["sub"], "role": user.get("role")}


# ======================================
# MONITORING
# ======================================

@router.get("/admin/monitor")
def monitor(user=Depends(verify_admin)):
    return system_stats()


@router.get("/admin/stats")
def stats(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_monitoring_stats(db)


# ======================================
# LOGS
# ======================================

@router.get("/admin/logs")
def logs(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_logs(db)


@router.get("/admin/security")
def security_logs(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_security_events(db)


# ======================================
# AI METRICS
# ======================================

@router.get("/admin/ai-metrics")
def ai_metrics():
    return get_ai_metrics()


# ======================================
# USERS
# ======================================

@router.get("/users")
def get_users(db: Session = Depends(get_db), user=Depends(verify_admin)):
    from app.database.model import User
    return db.query(User).all()


# ======================================
# CONVERSATIONS
# ======================================

@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_conversations(db)


@router.post("/conversations")
def new_conversation(title: str, db: Session = Depends(get_db), user=Depends(verify_admin)):
    return create_conversation(db, title)


@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: int, db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_messages(db, conversation_id)






