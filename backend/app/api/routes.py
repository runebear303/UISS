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

from app.services.security import detect_prompt_injection, sanitize_prompt

router = APIRouter()

MAX_INPUT_CHARS = 1000


# ======================================
# CHAT
# ======================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request, db: Session = Depends(get_db)):

    query = request.question.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Empty question")

    if len(query) > MAX_INPUT_CHARS:
        raise HTTPException(status_code=413, detail="Input too long")

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
async def chat_stream(request: ChatRequest, http_request: Request):

    query = request.question.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Empty question")

    if len(query) > MAX_INPUT_CHARS:
        raise HTTPException(status_code=413, detail="Input too long")

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

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    token = authenticate(request.username, request.password)

    if not token:
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






