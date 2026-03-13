from sqlalchemy.orm import Session
from app.database.model import Message


def create_message(db: Session, conversation_id, role, content):

    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )

    db.add(msg)
    db.commit()

    return msg


def get_messages(db: Session, conversation_id):

    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).all()