from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from typing import Any, Dict, Optional
from utils.config.config import config
import logging

logger = logging.getLogger(__name__)

class EncryptionManager:
    """Manager for handling data encryption at rest."""
    
    # Encryption key derivation settings
    SALT_LENGTH = 16
    ITERATIONS = 100000
    
    _instance = None
    _fernet = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EncryptionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the encryption manager."""
        if not self._fernet:
            self._initialize_fernet()
    
    def _initialize_fernet(self) -> None:
        """Initialize the Fernet encryption instance."""
        try:
            encryption_config = config.ENCRYPTION_CONFIG
            
            if not encryption_config['key']:
                raise RuntimeError("Encryption key not found in Vault")
            
            # Derive encryption key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=encryption_config['salt'].encode(),
                iterations=self.ITERATIONS
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(encryption_config['key'].encode()))
            
            # Initialize Fernet with derived key
            self._fernet = Fernet(derived_key)
            logger.info("✅ Encryption manager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption manager: {e}")
            raise

    def encrypt(self, data: str) -> str:
        """Encrypt a string."""
        if not self._fernet:
            self._initialize_fernet()
        try:
            return self._fernet.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string."""
        if not self._fernet:
            self._initialize_fernet()
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a dictionary."""
        encrypted = data.copy()
        for field in config.get_secret("secret/app/flask", "sensitive_fields", "").split(","):
            if field in encrypted and encrypted[field]:
                encrypted[field] = self.encrypt(str(encrypted[field]))
        return encrypted

    def decrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in a dictionary."""
        decrypted = data.copy()
        for field in config.get_secret("secret/app/flask", "sensitive_fields", "").split(","):
            if field in decrypted and decrypted[field]:
                decrypted[field] = self.decrypt(str(decrypted[field]))
        return decrypted 