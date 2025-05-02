import hvac
import os
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class VaultSecretsManager:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VaultSecretsManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._client:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the Vault client with proper authentication"""
        try:
            self._client = hvac.Client(
                url=os.getenv('VAULT_ADDR', 'http://vault:8200')
            )
            
            # Primary: Try Kubernetes authentication first
            if self._authenticate_kubernetes():
                return

            # Development only: Fallback to token authentication
            if os.getenv('FLASK_ENV') == 'development':
                token = self._read_token_from_secret()
                if token:
                    self._client.token = token
                    if self._client.is_authenticated():
                        logger.info("Successfully authenticated to Vault using development token")
                        return
                    logger.warning("Development token authentication failed")
            else:
                logger.error("Kubernetes authentication failed and token auth is not allowed in production")

        except Exception as e:
            logger.error(f"Vault initialization failed: {e}", exc_info=True)
            self._client = None

    def _authenticate_kubernetes(self) -> bool:
        """
        Authenticate using Kubernetes service account
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            # Check if we're running in a Kubernetes environment
            if not os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'):
                logger.debug("Not running in a Kubernetes environment")
                return False

            with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as f:
                jwt = f.read()
            
            self._client.auth.kubernetes.login(
                role='flask-auth',
                jwt=jwt
            )
            logger.info("Successfully authenticated to Vault using Kubernetes")
            return True
        except FileNotFoundError:
            logger.debug("No Kubernetes service account token found")
            return False
        except Exception as e:
            logger.error(f"Kubernetes authentication failed: {e}", exc_info=True)
            return False

    def _read_token_from_secret(self) -> Optional[str]:
        """
        Read Vault token from Docker secret (Development only)
        Returns:
            Optional[str]: Token if found and in development mode, None otherwise
        """
        if os.getenv('FLASK_ENV') != 'development':
            logger.warning("Attempted to use token authentication in non-development environment")
            return None

        try:
            with open('/run/secrets/vault_token', 'r') as f:
                logger.debug("Successfully read development Vault token from Docker secret")
                return f.read().strip()
        except FileNotFoundError:
            logger.debug("No Vault token found in Docker secrets")
            return None
        except Exception as e:
            logger.error(f"Error reading Vault token: {e}", exc_info=True)
            return None

    def get_secret(self, path: str, key: str) -> Optional[str]:
        """
        Get a secret from Vault with fallback to Docker secrets
        
        Args:
            path: The path in Vault (e.g., 'secret/app/flask')
            key: The specific key to retrieve
        
        Returns:
            The secret value or None if not found
        """
        if not self._client or not self._client.is_authenticated():
            logger.error("Vault client not initialized or not authenticated")
            return None

        try:
            # For KV v2, ensure path is in the correct format
            # First, remove any existing prefixes to get clean path
            clean_path = path
            if clean_path.startswith('secret/data/'):
                clean_path = clean_path[len('secret/data/'):]
            elif clean_path.startswith('secret/'):
                clean_path = clean_path[len('secret/'):]
            
            logger.debug(f"Attempting to read secret from path: {clean_path}")
            try:
                secret = self._client.secrets.kv.v2.read_secret_version(path=clean_path)
                if secret and 'data' in secret and 'data' in secret['data']:
                    value = secret['data']['data'].get(key)
                    if value is not None:
                        return str(value)
                    logger.debug(f"Key {key} not found in secret at path {clean_path}")
                    return None
                logger.debug(f"Invalid secret format at path {clean_path}")
                return None
            except Exception as e:
                logger.error(f"Failed to read secret at path {clean_path}: {e}")
                return None
        except Exception as e:
            logger.error(f"Failed to read secret from Vault: {e}", exc_info=True)
            return None

    def is_healthy(self) -> bool:
        """Check if Vault connection is healthy"""
        try:
            return bool(self._client and self._client.is_authenticated())
        except Exception:
            return False

# Global instance
vault_secrets = VaultSecretsManager() 