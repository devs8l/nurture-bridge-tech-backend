"""
Conversation Encryption for PHI Protection

Application-level encryption for conversation transcripts containing PHI.
Uses Fernet symmetric encryption (AES-128) with key derived from app secret.

Usage:
    from app_logging.conversation_encryption import ConversationEncryption
    
    encryptor = ConversationEncryption()
    
    # Encrypt for storage
    encrypted = encryptor.encrypt(conversation_dict)
    
    # Decrypt for processing
    conversation = encryptor.decrypt(encrypted_str)
"""

import json
import hashlib
import base64
from typing import Dict, Any
from cryptography.fernet import Fernet
from config.settings import settings
from app_logging.logger import get_logger

logger = get_logger(__name__)


class ConversationEncryption:
    """
    Encrypts and decrypts conversation transcripts for secure storage.
    
    Uses Fernet symmetric encryption (AES-128 CBC with HMAC authentication).
    Encryption key is derived from application SECRET_KEY to avoid additional key management.
    """
    
    def __init__(self):
        """Initialize encryption cipher with key derived from app secret."""
        # Derive 32-byte key from app secret using SHA-256
        key_material = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        
        # Fernet requires base64-encoded 32-byte key
        self.key = base64.urlsafe_b64encode(key_material)
        self.cipher = Fernet(self.key)
        
        logger.info("conversation_encryption_initialized")
    
    def encrypt(self, conversation: Dict[str, Any]) -> str:
        """
        Encrypt conversation dictionary to base64 string.
        
        Args:
            conversation: Conversation data as dict
            
        Returns:
            Base64-encoded encrypted string
            
        Example:
            >>> encryptor = ConversationEncryption()
            >>> encrypted = encryptor.encrypt({"messages": [...]})
            >>> type(encrypted)
            <class 'str'>
        """
        try:
            # Convert dict to JSON string
            json_str = json.dumps(conversation)
            
            # Encrypt (produces bytes)
            encrypted_bytes = self.cipher.encrypt(json_str.encode('utf-8'))
            
            # Encode to base64 string for database storage
            encrypted_str = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            logger.debug(
                "conversation_encrypted",
                original_size=len(json_str),
                encrypted_size=len(encrypted_str)
            )
            
            return encrypted_str
            
        except Exception as e:
            logger.error("conversation_encryption_failed", error=str(e))
            raise
    
    def decrypt(self, encrypted_str: str) -> Dict[str, Any]:
        """
        Decrypt base64 string back to conversation dictionary.
        
        Args:
            encrypted_str: Base64-encoded encrypted string
            
        Returns:
            Decrypted conversation as dict
            
        Raises:
            cryptography.fernet.InvalidToken: If decryption fails (corrupted data or wrong key)
            
        Example:
            >>> encryptor = ConversationEncryption()
            >>> conversation = encryptor.decrypt(encrypted_str)
            >>> type(conversation)
            <class 'dict'>
        """
        try:
            # Decode from base64 string to bytes
            encrypted_bytes = base64.b64decode(encrypted_str.encode('utf-8'))
            
            # Decrypt (produces bytes)
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            
            # Parse JSON
            json_str = decrypted_bytes.decode('utf-8')
            conversation = json.loads(json_str)
            
            logger.debug("conversation_decrypted", decrypted_size=len(json_str))
            
            return conversation
            
        except Exception as e:
            logger.error("conversation_decryption_failed", error=str(e))
            raise


# Singleton instance for reuse
_encryptor = None


def get_encryptor() -> ConversationEncryption:
    """Get singleton conversation encryptor instance."""
    global _encryptor
    if _encryptor is None:
        _encryptor = ConversationEncryption()
    return _encryptor
