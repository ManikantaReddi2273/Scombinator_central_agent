"""
Encryption service for tokens and passwords
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import bcrypt
from config import settings


class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self):
        """Initialize encryption with key from settings"""
        # Use ENCRYPTION_KEY directly as Fernet key (must be 32 bytes base64)
        # If key is not valid Fernet key, derive it
        try:
            # Try to use as Fernet key directly
            self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
        except Exception:
            # Derive key from ENCRYPTION_KEY if not valid Fernet key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b's_combinator_salt',  # In production, use random salt per encryption
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(settings.ENCRYPTION_KEY.encode()))
            self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string"""
        if not plaintext:
            return ""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string"""
        if not ciphertext:
            return ""
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False


# Singleton instance
encryption_service = EncryptionService()

