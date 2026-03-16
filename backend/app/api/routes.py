from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse, LoginRequest, TokenResponse
from app.services.ai_service import ask_ai_with_sources
from app.services.auth import authenticate
from app.services.dependencies import verify_admin
from app.services.monitor import system_stats
from app.services.metrics import get_ai_metrics
from app.services.llm.llm_orchestrator import ask_llm_stream
from app.rag.rag import search_docs
from app.database.db import get_db
from app.config import MAX_INPUT_CHARS
from app.crud.crud_conversation import create_conversation, get_conversations
from app.crud.crud_messsage import create_message, get_messages
import shutil
import os
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

# ======================================
# CHAT
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

    # 2. Beveiligingscheck (Prompt Injection)
    status, reason = detect_prompt_injection(query, user_ip)
    
    if status == "BLOCKED":
        # Log de aanval voordat we de foutmelding geven
        log_security_event(db, "PROMPT_INJECTION", f"Geblokkeerd: {reason}", user_ip)
        raise HTTPException(
            status_code=400, 
            detail="Je vraag bevat mogelijk onveilige instructies"
        )

    if status == "SUSPICIOUS":
        query = sanitize_prompt(query)

    # 3. AI Verwerking (RAG + LLM)
    result = ask_ai_with_sources(db, query)

    # 4. Opslaan in database
    try:
        conv_id = getattr(request, 'conversation_id', None)
        
        # Check of de conversatie echt bestaat in de DB
        from app.database.model import Conversation
        db_conv = None
        if conv_id:
            db_conv = db.query(Conversation).filter(Conversation.id == conv_id).first()

        # Als de ID niet bestaat of ongeldig is, maken we een nieuwe aan
        if not db_conv:
            print(f"INFO: Conversation ID {conv_id} niet gevonden. Nieuwe aanmaken...")
            new_c = Conversation(title=query[:30] + "...") # Gebruik begin van de vraag als titel
            db.add(new_c)
            db.commit()
            db.refresh(new_c)
            conv_id = new_c.id
            print(f"INFO: Nieuwe conversatie aangemaakt met ID: {conv_id}")

        # Nu kunnen we VEILIG de berichten opslaan
        create_message(db, conversation_id=conv_id, role="user", content=query)
        create_message(db, conversation_id=conv_id, role="assistant", content=result["answer"])
        
        # Update ook de result dict zodat de frontend de (nieuwe) ID weet
        result["conversation_id"] = conv_id

        # Loggen voor admin dashboard
        log_chat(
            db=db, 
            prompt=query, 
            response=result["answer"], 
            provider=result.get("provider", "local")
        )
        
    except Exception as e:
        # Dit is de ultieme veiligheid: de gebruiker krijgt GEEN error 
        # als alleen het opslaan mislukt. De AI heeft immers al geantwoord.
        db.rollback()
        print(f"FOUT bij database opslag (genegeerd voor gebruiker): {e}")

        # A. Sla de berichten op
        create_message(db, conversation_id=conv_id, role="user", content=query)
        create_message(db, conversation_id=conv_id, role="assistant", content=result["answer"])

        # B. Log AI Verbruik (Nieuw!)
        # Dit vult de statistieken voor je grafieken
        log_ai_usage(
            db=db,
            model_name=result.get("model", "tinyllama"),
            prompt_tokens=result.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=result.get("usage", {}).get("completion_tokens", 0),
            total_cost=result.get("cost", 0.0)
        )

        # C. Log Systeem Alert bij traagheid (Nieuw!)
        # Als TinyLlama er langer dan 10 seconden over doet, willen we dat weten
        if result.get("latency_ms", 0) > 10000:
            log_system_alert(
                db=db,
                level="WARNING",
                message=f"Hoge latency gedetecteerd: {result['latency_ms']}ms voor TinyLlama"
            )

        # D. Algemene chat log
        log_chat(db, query, result["answer"], result.get("provider", "local"))

    except Exception as e:
        # Als er iets misgaat in de logging, willen we een kritieke alert
        log_system_alert(db, level="CRITICAL", message=f"Logging crash: {str(e)}")
        print(f"Logging error: {e}")

    return result
  
# ======================================
# STREAM CHAT
# ======================================

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, http_request: Request, db: Session = Depends(get_db)):
    query = request.question.strip()
    user_ip = http_request.client.host

    # 1. Beveiliging & Logging
    status, reason = detect_prompt_injection(query, user_ip)
    if status == "BLOCKED":
        # Log de blokkade in je security_logs tabel
        log_security_event(db, "PROMPT_INJECTION", f"Stream geblokkeerd: {reason}", user_ip)
        raise HTTPException(status_code=400, detail="Onveilige vraag gedetecteerd")

    # 2. Sla de gebruikersvraag ALVAST op (voordat de stream start)
    try:
        conv_id = getattr(request, 'conversation_id', None)
        if conv_id:
            create_message(db, conv_id, "user", query)
    except Exception as e:
        print(f"Fout bij opslaan gebruikersvraag: {e}")

    # 3. RAG Zoekopdracht
    docs = search_docs(query)
    context_text = "\n\n".join([doc["text"] for doc in docs]) if docs else "Geen relevante documentatie gevonden."
    
    # Gebruik je beveiligde prompt generator
    final_prompt = secure_rag_prompt(query, context_text)

    # 4. De Stream Generator
    async def stream_generator():
        full_response = ""
        try:
            async for token in ask_llm_stream(final_prompt):
                full_response += token
                yield token
            
            # 5. Sla het AI-antwoord op NADAT de stream klaar is
            if full_response:
                create_message(db, request.conversation_id, "assistant", full_response)
                # Optioneel: log ook het verbruik
                log_chat(db, query, full_response, {}, "local-stream")
        except Exception as e:
            yield f"\n[Systeemfout: {str(e)}]"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

# ======================================
# LOGIN
# ======================================

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
# DOCUMENT MANAGEMENT
# ======================================

@router.post("/admin/upload")
async def upload_document(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    user=Depends(verify_admin)
):
    # 1. Pad bepalen
    upload_dir = "app/source/docs"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    file_path = os.path.join(upload_dir, file.filename)

    # 2. Bestand opslaan op schijf
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Opslagfout: {str(e)}")

    # 3. DIRECT VERWERKEN VOOR RAG
    from app.services.pdf_processor import process_pdf_to_rag
    chunks_created = process_pdf_to_rag(file_path, file.filename)

    # 4. Database metadata bijwerken
    from app.database.model import Document
    try:
        new_doc = Document(
            title=file.filename,
            source=file.filename,
            text=f"Verwerkt: {chunks_created} segmenten."
        )
        db.add(new_doc)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")

    return {
        "message": "Upload en verwerking geslaagd", 
        "filename": file.filename, 
        "chunks": chunks_created
    }

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






