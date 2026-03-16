from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
import datetime
from app.database.model import ChatLog, SystemLog, SecurityLog, Conversation, Message

# =========================
# CHAT LOGGING
# =========================
def log_chat(
    db: Session,
    prompt: any, 
    response: str,
    provider: str,
    usage: dict | None = None,
    cost: float = 0.0
):
    """
    Slaat de volledige chat inclusief tokens en kosten op in de chat_logs tabel.
    Dit is nu de centrale bron voor alle AI-statistieken.
    """
    clean_prompt = str(prompt)
    clean_response = str(response)
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
    """Slaat systeemmeldingen en fouten op voor het dashboard."""
    system_log = SystemLog(level=level, message=message, module=module)
    try:
        db.add(system_log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Fout bij opslaan system_log: {e}")

# =========================
# SECURITY LOGGING
# =========================
def log_security_event(db: Session, event_type: str, message: str, ip_address: str = ""):
    """Logt beveiligingsincidenten zoals prompt injections."""
    security_log = SecurityLog(event_type=event_type, message=message, ip_address=ip_address)
    try:
        db.add(security_log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Fout bij opslaan security_log: {e}")

# =========================
# MONITORING STATS (Dashboard Data)
# =========================
def get_monitoring_stats(db: Session) -> dict:
    """Haalt de statistieken op uit de ChatLog tabel voor de grafieken."""
    total_conversations = db.query(func.count(ChatLog.id)).scalar() or 0
    total_ai_cost = db.query(func.sum(ChatLog.cost)).scalar() or 0
    avg_tokens = db.query(func.avg(ChatLog.total_tokens)).scalar() or 0

    return {
        "total_conversations": total_conversations,
        "total_ai_cost": round(total_ai_cost, 6),
        "average_tokens_per_request": round(avg_tokens, 2)
    }

# =========================
# CLOUD COST TODAY
# =========================
def get_today_cloud_cost(db: Session) -> float:
    """Berekent de totale AI kosten van de huidige dag."""
    today = date.today()
    total_cost = db.query(func.sum(ChatLog.cost))\
                   .filter(func.date(ChatLog.created_at) == today)\
                   .scalar()
    return total_cost or 0.0

# =========================
# CONVERSATION & MESSAGES (Helper functies)
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
# RETRIEVAL FUNCTIONS (Voor Admin Dashboard)
# =========================
def get_logs(db: Session):
    """Haalt de meest recente chats op voor de log-view."""
    return db.query(ChatLog).order_by(ChatLog.created_at.desc()).limit(100).all()

def get_security_events(db: Session):
    """Haalt de meest recente beveiligingsincidenten op."""
    return db.query(SecurityLog).order_by(SecurityLog.created_at.desc()).all()