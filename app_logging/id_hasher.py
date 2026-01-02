"""
ID Hashing for Privacy-Preserving Logging

Hashes UUIDs and emails using SHA-256 with application secret salt.
This allows correlation in logs while preventing re-identification of individuals.

Usage:
    from app_logging.id_hasher import hash_id, hash_email
    
    logger.info("user_created", user_id_hash=hash_id(user.id))
    logger.info("login_attempt", email_hash=hash_email(email))
"""

import hashlib
from typing import Optional
from config.settings import settings


def hash_id(id_value: Optional[str]) -> str:
    """
    Hash a UUID or ID for logging purposes.
    
    Uses SHA-256 with application secret as salt to create a consistent hash
    that can be used for correlation across logs without exposing the actual ID.
    
    Args:
        id_value: UUID or ID string to hash
        
    Returns:
        First 12 characters of SHA-256 hash for log readability
        Returns "none" if id_value is None or empty
        
    Example:
        >>> hash_id("123e4567-e89b-12d3-a456-426614174000")
        "a1b2c3d4e5f6"
    """
    if not id_value:
        return "none"
    
    # Use app secret as salt to ensure hashes are app-specific
    salted = f"{settings.SECRET_KEY}:{id_value}"
    hashed = hashlib.sha256(salted.encode()).hexdigest()
    
    # Return shortened hash (first 12 chars) for log readability
    # Still provides 2^48 unique values (collision-resistant for logging)
    return hashed[:12]


def hash_email(email: Optional[str]) -> str:
    """
    Hash email address for logging purposes.
    
    Uses SHA-256 with application secret as salt. Same user logging in
    multiple times will produce the same hash, enabling correlation.
    
    Args:
        email: Email address to hash
        
    Returns:
        First 12 characters of SHA-256 hash
        Returns "none" if email is None or empty
        
    Example:
        >>> hash_email("user@example.com")
        "f7a8b9c0d1e2"
    """
    if not email:
        return "none"
    
    # Normalize email to lowercase for consistent hashing
    email_normalized = email.lower().strip()
    
    salted = f"{settings.SECRET_KEY}:{email_normalized}"
    hashed = hashlib.sha256(salted.encode()).hexdigest()
    return hashed[:12]
