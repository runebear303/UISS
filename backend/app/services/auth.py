from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
import secrets

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", 2))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

if not ADMIN_USER or not ADMIN_PASS:
    raise ValueError("Admin credentials are not properly configured")


def authenticate(username: str, password: str):
    """
    Authenticeert admin gebruiker en genereert JWT.
    """

    if not (
        secrets.compare_digest(username, ADMIN_USER) and
        secrets.compare_digest(password, ADMIN_PASS)
    ):
        return None

    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": username,
        "role": "admin",
        "iat": datetime.utcnow(),
        "exp": expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    """
    Decodeert JWT en retourneert payload indien geldig.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None