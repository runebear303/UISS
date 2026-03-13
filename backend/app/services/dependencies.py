from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth import decode_token

security = HTTPBearer()


# ===============================
# TOKEN VERIFICATIE
# ===============================

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Verifieert JWT token en retourneert payload.
    """

    token = credentials.credentials
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return payload


# ===============================
# ADMIN ONLY ENFORCEMENT
# ===============================

def verify_admin(
    payload: dict = Depends(verify_token)
):
    """
    Controleert of gebruiker admin rol heeft.
    Alleen admin krijgt toegang.
    """

    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return payload