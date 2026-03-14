from datetime import datetime, timedelta
from jose import jwt, JWTError
import os
import bcrypt
from sqlalchemy.orm import Session
from app.database.model import User  # Zorg dat dit pad klopt

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", 2))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

def authenticate(db: Session, username: str, password: str):
    """
    Controleert de gebruiker tegen de database en geeft een JWT terug.
    """
    # 1. Zoek de gebruiker in de MySQL database
    user = db.query(User).filter(User.username == username).first()

    if not user:
        print(f"Inlogpoging mislukt: Gebruiker {username} niet gevonden.")
        return None

    # 2. Controleer of het wachtwoord klopt met de opgeslagen hash
    # We zetten de strings om naar bytes met .encode('utf-8')
    password_byte = password.encode('utf-8')
    hashed_byte = user.hashed_password.encode('utf-8')

    if not bcrypt.checkpw(password_byte, hashed_byte):
        print(f"Inlogpoging mislukt: Wachtwoord onjuist voor {username}.")
        return None

    # 3. Genereer de token als alles klopt
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": user.username,
        "role": user.role,
        "iat": datetime.utcnow(),
        "exp": expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)