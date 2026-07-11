"""backend/utils/auth.py — JWT helpers and password hashing"""
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET  = os.getenv("JWT_SECRET", "photogram-secret-change-in-prod")
ALGO    = "HS256"
EXPIRY  = 72   # hours

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer  = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(pw, hashed)


def create_token(user_id: int, username: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=EXPIRY)
    return jwt.encode({"sub": str(user_id), "username": username, "exp": exp}, SECRET, algorithm=ALGO)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def current_user_id(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(creds.credentials)
    return int(payload["sub"])


async def optional_user_id(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
        return int(payload["sub"])
    except Exception:
        return None