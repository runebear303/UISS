from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# ===============================
# CHAT
# ===============================

class Source(BaseModel):
    text: str
    source: Optional[str] = None
    page: Optional[int] = None
    chunk_id: Optional[int] = None
    score: Optional[float] = None


class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None



class ChatResponse(BaseModel):
    conversation_id: Optional[int] = None
    sources: List[Any] = []
    confidence: float = 0.0
    cost: float = 0.0
    latency_ms: int = 0
    usage: Optional[Dict[str, Any]] = None


# ===============================
# AUTH
# ===============================

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"