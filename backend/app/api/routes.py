from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse, LoginRequest, TokenResponse
from app.services.ai_service import ask_ai_with_sources
from app.services.auth import authenticate
from app.services.dependencies import verify_admin
from app.services.monitor import system_stats
from app.database.db import get_db
from app.config import MAX_INPUT_CHARS
from app.crud.crud_conversation import create_conversation, get_conversations
from app.crud.crud_messsage import create_message, get_messages
import shutil
import os

# Importeer de gecorrigeerde functies uit je nieuwe logger.py
from app.services.logger import (
    log_chat, 
    log_system_alert, 
    log_security_event, 
    get_logs, 
    get_security_events, 
    get_monitoring_stats
)
from app.services.security import detect_prompt_injection, sanitize_prompt

router = APIRouter()

# ======================================
# CHAT ENDPOINT
# ======================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request, db: Session = Depends(get_db)):
    query = request.question.strip()
    user_ip = http_request.client.host

    # 1. Basis Validatie
    if not query:
        raise HTTPException(status_code=400, detail="Vraag is leeg")
    if len(query) > MAX_INPUT_CHARS:
        raise HTTPException(status_code=413, detail="Input te lang")

    # 2. Beveiligingscheck
    status, reason = detect_prompt_injection(query, user_ip)
    if status == "BLOCKED":
        log_security_event(db, "PROMPT_INJECTION", f"Geblokkeerd: {reason}", user_ip)
        raise HTTPException(status_code=400, detail="Onveilige vraag gedetecteerd")

    if status == "SUSPICIOUS":
        query = sanitize_prompt(query)

    # 3. AI Verwerking (RAG + LLM)
    incoming_id = getattr(request, 'conversation_id', None)
    result = ask_ai_with_sources(db, vraag=query, conversation_id=incoming_id)

    # 4. Database opslag & Logging
    try:
        from app.database.model import Conversation
        conv_id = incoming_id

        # Controleer of maak conversatie aan
        db_conv = None
        if conv_id:
            db_conv = db.query(Conversation).filter(Conversation.id == conv_id).first()

        if not db_conv:
            # Maak een nieuwe aan als de ID niet bestaat of None is
            new_c = Conversation(title=query[:30] + "...")
            db.add(new_c)
            db.commit()
            db.refresh(new_c)
            conv_id = new_c.id
        
        # Sla de berichten op voor de chat-geschiedenis
        create_message(db, conversation_id=conv_id, role="user", content=query)
        create_message(db, conversation_id=conv_id, role="assistant", content=result["answer"])
        
        # Update resultaat zodat de frontend de (nieuwe) ID weet
        result["conversation_id"] = conv_id

        # --- Eén centrale log-actie voor het dashboard ---
        log_chat(
            db=db,
            prompt=query,
            response=result["answer"],
            provider=result.get("provider", "local"),
            usage=result.get("usage"),
            cost=result.get("cost", 0.0)
        )

        # Log alert bij hoge latency
        if result.get("latency_ms", 0) > 10000:
            log_system_alert(db, "WARNING", f"Hoge latency: {result['latency_ms']}ms", module="chat")

    except Exception as e:
        db.rollback()
        print(f"Logging/Database error (genegeerd voor gebruiker): {e}")
        # We blokkeren de return niet, zodat de gebruiker het antwoord krijgt

    return result

# ======================================
# AUTH & ADMIN
# ======================================

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    token = authenticate(db, request.username, request.password)
    if not token:
        raise HTTPException(status_code=401, detail="Ongeldige inloggegevens")
    return {"access_token": token, "token_type": "bearer"}

@router.get("/admin/stats")
def stats(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_monitoring_stats(db)

@router.get("/admin/logs")
def logs(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_logs(db)

@router.get("/admin/security")
def security_logs(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_security_events(db)

# ======================================
# DOCUMENT MANAGEMENT
# ======================================

@router.post("/admin/upload")
async def upload_document(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    user=Depends(verify_admin)
):
    upload_dir = "app/source/docs"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    from app.services.pdf_processor import process_pdf_to_rag
    chunks_created = process_pdf_to_rag(file_path, file.filename)

    from app.database.model import Document
    new_doc = Document(title=file.filename, source=file.filename, text=f"Verwerkt: {chunks_created} chunks")
    db.add(new_doc)
    db.commit()

    return {"message": "Upload succesvol", "chunks": chunks_created}

# ======================================
# CONVERSATIONS
# ======================================

@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_conversations(db)

@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: int, db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_messages(db, conversation_id)






