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
    answer: str
    # Verander List[Source] naar List[Any] om validatiefouten te voorkomen
    sources: List[Any] = [] 
    confidence: float = 0.0
    provider: str
    cost: float = 0.0
    latency_ms: int = 0
    usage: Optional[Dict[str, Any]] = None
    # VOEG DEZE TOE: je routes.py probeert dit te sturen, 
    # maar het stond nog niet in je schema!
    conversation_id: Optional[int] = None


# ===============================
# AUTH
# ===============================

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"