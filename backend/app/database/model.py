from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(100))
    role = Column(String(20), default="user") # 'admin' of 'user'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatLog(Base):

    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True)

    prompt = Column(Text)

    response = Column(Text)

    provider = Column(String(50))

    prompt_tokens = Column(Integer)

    completion_tokens = Column(Integer)

    total_tokens = Column(Integer)

    cost = Column(Float)

    created_at = Column(DateTime, server_default=func.now())


class Document(Base):

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)

    title = Column(String(255))

    text = Column(Text)

    source = Column(String(255))

    created_at = Column(DateTime, server_default=func.now())


class SystemLog(Base):

    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True)

    level = Column(String(20))

    message = Column(Text)

    module = Column(String(100))

    created_at = Column(DateTime, server_default=func.now())


class SecurityLog(Base):

    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True)

    event_type = Column(String(50))

    message = Column(Text)

    ip_address = Column(String(45))

    created_at = Column(DateTime, server_default=func.now())


class AIMetric(Base):

    __tablename__ = "ai_metrics"

    id = Column(Integer, primary_key=True)

    provider = Column(String(50))

    total_requests = Column(Integer)

    total_tokens = Column(Integer)

    total_cost = Column(Float)

    created_at = Column(DateTime, server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
class LLMLog(Base):
    __tablename__ = "llm_logs"

    id = Column(Integer, primary_key=True, index=True)
    prompt_length = Column(Integer)  # Lengte van de vraag
    response_time = Column(Float)    # Latency in seconden of ms
    docs_retrieved = Column(Integer) # Hoeveel chunks k=X vond
    status = Column(String(20))      # 'SUCCESS' of 'ERROR'
    created_at = Column(DateTime(timezone=True), server_default=func.now())  