from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import re

# Configuration - Load from environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")

security = HTTPBearer()

# Setup password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Check if a plain text password matches a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Create a hash from a plain text password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

def get_current_user_id(token: HTTPAuthorizationCredentials = Depends(security)) -> int:
    payload = verify_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return int(user_id)

def validate_password_complexity(password: str) -> bool:
    """Check password meets complexity requirements"""
    if (len(password) >= 8 and 
        any(c.isupper() for c in password) and 
        any(c.islower() for c in password) and 
        any(c.isdigit() for c in password)):
        return True
    return False

def sanitize_input(input_string: str) -> str:
    """Basic input sanitization"""
    return re.sub(r'[<>&\"\']', '', input_string).strip()