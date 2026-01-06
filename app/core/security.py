"""
Core Security Module
JWT configuration, Password Hashing, and Token Utilities.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import hashlib

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

def hash_refresh_token(token: str) -> str:
    """
    Hash refresh token using SHA-256 before database storage.
    NEVER store raw refresh tokens in the database.
    """
    return hashlib.sha256(token.encode()).hexdigest()

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

def create_refresh_token(user_id: str, session_id: str) -> str:
    """
    Create JWT refresh token with session ID.
    
    Args:
        user_id: User's UUID
        session_id: Session UUID for tracking
    
    Returns:
        JWT refresh token string
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "sid": session_id,  # Session ID for validation
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    header = {"alg": ALGORITHM}
    
    return jwt.encode(header, payload, SECRET_KEY).decode("utf-8")

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify JWT access token."""
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

def decode_refresh_token(token: str) -> tuple[str, str]:
    """
    Decode and verify JWT refresh token.
    
    Returns:
        Tuple of (user_id, session_id)
    
    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(token, SECRET_KEY)
        
        # CRITICAL: Validate token type to prevent access token reuse
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Expected refresh token"},
            )
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "TOKEN_EXPIRED", "message": "Refresh token has expired"},
            )
        
        # Extract user_id from 'sub' claim
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Invalid refresh token - missing user identifier"},
            )
        
        # Extract session_id from 'sid' claim
        session_id = payload.get("sid")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_TOKEN", "message": "Invalid refresh token - missing session identifier"},
            )
        
        return user_id, session_id
    except JoseError as e:
        logger.error("refresh_token_decode_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Could not validate refresh token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

# ============================================================================
# COOKIE MANAGEMENT
# ============================================================================

def set_refresh_token_cookie(response, refresh_token: str) -> None:
    """
    Set HttpOnly refresh token cookie.
    
    Security features:
    - HttpOnly: Prevents JavaScript access (XSS protection)
    - Secure: HTTPS-only in production (disabled for localhost testing)
    - SameSite=lax: CSRF protection
    - Domain: None to work with localhost
    """
    from fastapi import Response
    
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=refresh_token,
        domain=None,  # Let browser set domain automatically
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        secure=False,  # Must be False for localhost testing (http)
        samesite=settings.SESSION_COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # Convert days to seconds
    )

def clear_refresh_token_cookie(response) -> None:
    """
    Clear refresh token cookie on logout.
    Sets expiry to past and clears value.
    """
    from fastapi import Response
    
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME
    )
