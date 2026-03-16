from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session
import shutil
import os

# Schemas & Database
from app.models.schemas import ChatRequest, ChatResponse, LoginRequest, TokenResponse
from app.database.db import get_db
from app.database.model import Conversation, Document

# Services
from app.services.ai_service import ask_ai_with_sources
from app.services.auth import authenticate
from app.services.dependencies import verify_admin
from app.services.security import detect_prompt_injection, sanitize_prompt
from app.config import MAX_INPUT_CHARS

# CRUD & Logging
from app.crud.crud_conversation import get_conversations
from app.crud.crud_messsage import create_message, get_messages
from app.services.logger import (
    log_chat, 
    log_system_alert, 
    log_security_event, 
    get_logs, 
    get_security_events, 
    get_monitoring_stats
)

router = APIRouter()

# ======================================
# CHAT ENDPOINT
# ======================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request, db: Session = Depends(get_db)):
    query = request.question.strip()
    user_ip = http_request.client.host

    # 1. Validatie (BEHOUDEN)
    if not query:
        raise HTTPException(status_code=400, detail="Vraag is leeg")
    if len(query) > MAX_INPUT_CHARS:
        raise HTTPException(status_code=413, detail="Input te lang")

    # 2. Security Scan (BEHOUDEN)
    status, reason = detect_prompt_injection(query, user_ip)
    if status == "BLOCKED":
        log_security_event(db, "PROMPT_INJECTION", f"Geblokkeerd: {reason}", user_ip)
        raise HTTPException(status_code=400, detail="Onveilige vraag gedetecteerd")
    
    if status == "SUSPICIOUS":
        query = sanitize_prompt(query)

    # 3. AI Processing (AANGEPAST NAAR JOUW RAG.PY)
    # Importeer get_answer hier of bovenin je bestand
    from app.rag.rag import get_answer 
    
    incoming_id = getattr(request, 'conversation_id', None)
    
    # We roepen nu jouw nieuwe get_answer aan uit rag.py
    answer_text = get_answer(query)
    
    # Maak het resultaat object handmatig aan zoals je oude ask_ai_with_sources dat deed
    result = {
        "answer": answer_text,
        "conversation_id": incoming_id,
        "provider": "local_rag"
    }

    # 4. Opslag & Logging (BEHOUDEN - Zorgt dat je chatgeschiedenis werkt!)
    try:
        conv_id = incoming_id
        db_conv = db.query(Conversation).filter(Conversation.id == conv_id).first() if conv_id else None

        if not db_conv:
            new_c = Conversation(title=query[:30] + "...")
            db.add(new_c)
            db.commit()
            db.refresh(new_c)
            conv_id = new_c.id
        
        create_message(db, conversation_id=conv_id, role="user", content=query)
        create_message(db, conversation_id=conv_id, role="assistant", content=result["answer"])
        
        result["conversation_id"] = conv_id

        log_chat(
            db=db,
            prompt=query,
            response=result["answer"],
            provider=result["provider"],
            usage={"total_tokens": len(answer_text.split())},
            cost=0.0
        )

    except Exception as e:
        db.rollback()
        print(f"Achtergrond logging fout: {e}")

    return result

# ======================================
# PUBLIC CONVERSATION ENDPOINTS (Geen verify_admin nodig)
# ======================================

@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db)):
    """Haalt alle gesprekken op voor de sidebar."""
    return get_conversations(db)

@router.get("/conversations/{conversation_id}/messages")
def conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    """Haalt de chat-geschiedenis op voor een specifiek gesprek."""
    return get_messages(db, conversation_id)

# ======================================
# ADMIN ENDPOINTS (Strikt beveiligd)
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

@router.get("/admin/security")
def security_logs(db: Session = Depends(get_db), user=Depends(verify_admin)):
    return get_security_events(db)

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

    # RAG Verwerking
    from app.services.pdf_processor import process_pdf_to_rag
    chunks_created = process_pdf_to_rag(file_path, file.filename)

    new_doc = Document(title=file.filename, source=file.filename, text=f"Chunks: {chunks_created}")
    db.add(new_doc)
    db.commit()

    return {"message": "Upload succesvol", "chunks": chunks_created}






