"""
Core Security Module
JWT configuration, Password Hashing, and Token Utilities.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from authlib.jose import jwt, JoseError
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from passlib.context import CryptContext

from config.settings import settings
from app_logging.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# PASSWORD HASHING
# ============================================================================

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4,
)

def hash_password(password: str) -> str:
    """Hash password using Argon2."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

# ============================================================================
# JWT CONFIGURATION
# ============================================================================

ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

security_scheme = HTTPBearer()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})
    header = {"alg": ALGORITHM}
    
    return jwt.encode(header, to_encode, SECRET_KEY).decode("utf-8")

def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    header = {"alg": ALGORITHM}
    
    return jwt.encode(header, payload, SECRET_KEY).decode("utf-8")

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY)
        
        # Validation
        if payload.get("type") != "access":
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
            
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
            
        return payload
    except JoseError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
