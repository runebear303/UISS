from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import os
import bcrypt
from sqlalchemy.orm import Session
from app.database.model import User

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", 24)) # 24 uur is fijner tijdens dev

def create_access_token(data: dict):
    """Genereert een JWT token op basis van meegegeven data."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({
        "iat": datetime.now(timezone.utc),
        "exp": expire
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate(db: Session, username: str, password: str):
    """Controleert de gebruiker en geeft een token terug."""
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return None

    # bcrypt check
    if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        return None

    # Gebruik de nieuwe functie voor de token
    token_data = {"sub": user.username, "role": user.role}
    return create_access_token(token_data)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None