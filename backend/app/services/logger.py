from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.database.model import ChatLog, SystemLog, SecurityLog, AIMetric, Conversation, Message

# =========================
# CHAT LOGGING
# =========================
def log_chat(
    db: Session,
    prompt: any, # Veranderd naar any voor robuustheid
    response: str,
    provider: str,
    usage: dict | None = None,
    cost: float = 0.0
):
    # --- STAP C FIX: VEILIGHEID ---
    # Forceer prompt en response naar string. 
    # Dit voorkomt dat Pydantic objecten de DB laten crashen.
    clean_prompt = str(prompt)
    clean_response = str(response)

    # Zorg dat usage ALTIJD een dictionary is, ook als er None of een string komt
    safe_usage = usage if isinstance(usage, dict) else {}

    chat = ChatLog(
        prompt=clean_prompt,
        response=clean_response,
        provider=provider,
        prompt_tokens=safe_usage.get("prompt_tokens", 0),
        completion_tokens=safe_usage.get("completion_tokens", 0),
        total_tokens=safe_usage.get("total_tokens", 0),
        cost=cost
    )
    
    try:
        db.add(chat)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"DATABASE ERROR in log_chat: {e}")

# =========================
# SYSTEM LOGGING
# =========================
def log_system_alert(db: Session, level: str, message: str, module: str = ""):
    system_log = SystemLog(level=level, message=message, module=module)
    db.add(system_log)
    db.commit()

# =========================
# SECURITY LOGGING
# =========================
def log_security_event(db: Session, event_type: str, message: str, ip_address: str = ""):
    security_log = SecurityLog(event_type=event_type, message=message, ip_address=ip_address)
    db.add(security_log)
    db.commit()

# =========================
# AI USAGE LOGGING
# =========================
def log_ai_usage(db: Session, provider: str, usage: dict | None = None, cost: float = 0.0):
    # Ook hier veiligheid toevoegen voor de usage dictionary
    safe_usage = usage if isinstance(usage, dict) else {}
    
    ai_log = AIMetric(
        provider=provider,
        total_requests=1,
        total_tokens=safe_usage.get("total_tokens", 0),
        total_cost=cost
    )
    try:
        db.add(ai_log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"DATABASE ERROR in log_ai_usage: {e}")

# =========================
# MONITORING STATS
# =========================
def get_monitoring_stats(db: Session) -> dict:
    total_conversations = db.query(func.count(ChatLog.id)).scalar()
    total_ai_cost = db.query(func.sum(AIMetric.total_cost)).scalar() or 0
    avg_tokens = db.query(func.avg(AIMetric.total_tokens)).scalar() or 0

    return {
        "total_conversations": total_conversations,
        "total_ai_cost": round(total_ai_cost, 6),
        "average_tokens_per_request": round(avg_tokens, 2)
    }

# =========================
# CLOUD COST TODAY
# =========================
def get_today_cloud_cost(db: Session) -> float:
    today = date.today()
    total_cost = db.query(func.sum(AIMetric.total_cost))\
                   .filter(func.date(AIMetric.created_at) == today)\
                   .scalar()
    return total_cost or 0.0

# =========================
# CONVERSATION & MESSAGES LOGGING
# =========================
def log_conversation(db: Session, title: str) -> Conversation:
    conv = Conversation(title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def log_message(db: Session, conversation: Conversation, role: str, content: str) -> Message:
    msg = Message(conversation_id=conversation.id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# =========================
# RETRIEVAL FUNCTIONS
# =========================
def get_logs(db: Session):
    return db.query(ChatLog).order_by(ChatLog.created_at.desc()).all()

def get_security_events(db: Session):
    return db.query(SecurityLog).order_by(SecurityLog.created_at.desc()).all()