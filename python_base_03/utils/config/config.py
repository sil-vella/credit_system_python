import os
from .vault_secrets import vault_secrets
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class Config:
    """
    Central configuration class that handles all secret management through Vault.
    This is the ONLY point of access for secrets in the application.
    
    Usage:
        from utils.config.config import config
        
        # Get a secret
        secret = config.get_secret("secret/app/flask", "key", "default")
        
        # Use predefined configurations
        mongodb_uri = config.MONGODB_URI
        redis_config = config.REDIS_CONFIG
        flask_config = config.FLASK_CONFIG
    """
    
    @staticmethod
    def get_secret(vault_path: str, key: str, default: Any = None) -> Optional[str]:
        """
        Get a secret exclusively from Vault
        
        Args:
            vault_path: The path in Vault (e.g., 'secret/app/flask')
            key: The specific key to retrieve
            default: Default value if secret is not found
        
        Returns:
            The secret value or default if not found
        """
        try:
            value = vault_secrets.get_secret(vault_path, key)
            if value is not None:
                return value
            
            if default is not None:
                logger.warning(f"Secret {key} not found in Vault path {vault_path}, using default value")
                return str(default)
            
            logger.error(f"Secret {key} not found in Vault path {vault_path} and no default provided")
            return None
        except Exception as e:
            logger.error(f"Error retrieving secret {key} from Vault: {e}")
            return default if default is not None else None

    # MongoDB Configuration
    @property
    def MONGODB_URI(self) -> str:
        host = self.get_secret("secret/app/mongodb", "host", "mongodb")
        port = self.get_secret("secret/app/mongodb", "port", "27017")
        user = self.get_secret("secret/app/mongodb", "root_username", "root")
        password = self.get_secret("secret/app/mongodb", "root_password")
        db = self.get_secret("secret/app/mongodb", "db_name", "credit_system")
        
        if not password:
            raise ValueError("MongoDB password not found in Vault")
        
        return f"mongodb://{user}:{password}@{host}:{port}/{db}?authSource=admin"

    # Redis Configuration
    @property
    def REDIS_CONFIG(self) -> dict:
        return {
            'host': self.get_secret("secret/app/redis", "host", "redis"),
            'port': int(self.get_secret("secret/app/redis", "port", "6379")),
            'password': self.get_secret("secret/app/redis", "password", "redis"),
            'db': int(self.get_secret("secret/app/redis", "db", "0")),
            'ssl': self.get_secret("secret/app/redis", "ssl", "false").lower() == "true",
            'ssl_verify_mode': self.get_secret("secret/app/redis", "ssl_verify_mode", "none")
        }

    # Flask Configuration
    @property
    def FLASK_CONFIG(self) -> dict:
        return {
            'SECRET_KEY': self.get_secret("secret/app/flask", "secret_key"),
            'JWT_SECRET_KEY': self.get_secret("secret/app/flask", "jwt_key"),
            'SERVICE_NAME': self.get_secret("secret/app/flask", "service_name", "flask"),
            'PORT': int(self.get_secret("secret/app/flask", "port", "5000"))
        }

    # Encryption Configuration
    @property
    def ENCRYPTION_CONFIG(self) -> dict:
        return {
            'key': self.get_secret("secret/app/flask", "encryption_key"),
            'salt': self.get_secret("secret/app/flask", "encryption_salt", "default_salt_123")
        }

    # Stripe Configuration
    @property
    def STRIPE_CONFIG(self) -> dict:
        return {
            'secret_key': self.get_secret("secret/app/stripe", "secret_key"),
            'api_version': self.get_secret("secret/app/stripe", "api_version", "2022-11-15")
        }

# Global instance
config = Config()

def get_secret(secret_name: str, vault_path: str = None, vault_key: str = None) -> str:
    """
    Get a secret with the following precedence:
    1. Vault (if path and key provided)
    2. Docker secrets
    3. Environment variables
    """
    # Try Vault first if path and key are provided
    if vault_path and vault_key:
        vault_value = vault_secrets.get_secret(vault_path, vault_key)
        if vault_value is not None:
            return vault_value

    # Try Docker secrets
    secret_value = read_secret_file(secret_name)
    if secret_value is not None:
        return secret_value

    # Fall back to environment variables
    return os.getenv(secret_name)

# Helper to read secrets from files (returns None if not found)
def read_secret_file(secret_name: str) -> str:
    path = f"/run/secrets/{secret_name}"
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except Exception:
        return None

class Config:
    # Flask Configuration
    FLASK_SERVICE_NAME = get_secret("flask_service_name", "secret/app/flask", "service_name") or "flask"
    FLASK_PORT = int(get_secret("flask_port", "secret/app/flask", "port") or "5000")
    PYTHONPATH = get_secret("pythonpath", "secret/app/flask", "pythonpath") or os.getenv("PYTHONPATH", "/app")

    # MongoDB Configuration
    MONGODB_SERVICE_NAME = get_secret("mongodb_service_name", "secret/app/mongodb", "service_name") or "mongodb"
    MONGODB_ROOT_USER = get_secret("mongodb_root_user", "secret/app/mongodb", "root_username") or "root"
    MONGODB_ROOT_PASSWORD = get_secret("mongodb_root_password", "secret/app/mongodb", "root_password") or "rootpassword"
    MONGODB_USER = get_secret("mongodb_user", "secret/app/mongodb", "username") or "credit_system_user"
    MONGODB_PASSWORD = get_secret("mongodb_user_password", "secret/app/mongodb", "password") or "credit_system_password"
    MONGODB_DB_NAME = get_secret("mongodb_db_name", "secret/app/mongodb", "db_name") or "credit_system"
    MONGODB_PORT = int(get_secret("mongodb_port", "secret/app/mongodb", "port") or "27017")

    # Redis Configuration
    REDIS_SERVICE_NAME = get_secret("redis_service_name", "secret/app/redis", "service_name") or "redis"
    REDIS_HOST = get_secret("redis_host", "secret/app/redis", "host") or "redis"
    REDIS_PORT = int(get_secret("redis_port", "secret/app/redis", "port") or "6379")
    REDIS_PASSWORD = get_secret("redis_password", "secret/app/redis", "password")

    # Debug mode
    DEBUG = get_secret("FLASK_DEBUG", "secret/app/flask", "debug").lower() in ("true", "1")

    # App URL Configuration
    APP_URL = get_secret("APP_URL", "secret/app/flask", "url") or os.getenv("APP_URL", "http://localhost:5000")

    # External Credit System Configuration
    CREDIT_SYSTEM_URL = get_secret("CREDIT_SYSTEM_URL", "secret/app/flask", "url") or os.getenv("CREDIT_SYSTEM_URL", "http://localhost:8000")
    CREDIT_SYSTEM_API_KEY = get_secret("CREDIT_SYSTEM_API_KEY", "secret/app/flask", "api_key") or "test_api_key"

    # JWT Configuration
    JWT_SECRET_KEY = get_secret("jwt_secret_key", "secret/app/flask", "jwt_key") or "your-super-secret-key-change-in-production"
    JWT_ACCESS_TOKEN_EXPIRES = int(get_secret("JWT_ACCESS_TOKEN_EXPIRES", "secret/app/flask", "access_token_expires") or "3600")  # 1 hour in seconds
    JWT_REFRESH_TOKEN_EXPIRES = int(get_secret("JWT_REFRESH_TOKEN_EXPIRES", "secret/app/flask", "refresh_token_expires") or "604800")  # 7 days in seconds
    JWT_ALGORITHM = get_secret("JWT_ALGORITHM", "secret/app/flask", "jwt_algorithm") or "HS256"
    JWT_TOKEN_TYPE = get_secret("JWT_TOKEN_TYPE", "secret/app/flask", "jwt_token_type") or "bearer"
    JWT_HEADER_NAME = get_secret("JWT_HEADER_NAME", "secret/app/flask", "jwt_header_name") or "Authorization"
    JWT_HEADER_TYPE = get_secret("JWT_HEADER_TYPE", "secret/app/flask", "jwt_header_type") or "Bearer"
    JWT_QUERY_STRING_NAME = get_secret("JWT_QUERY_STRING_NAME", "secret/app/flask", "jwt_query_string_name") or "token"
    JWT_QUERY_STRING_VALUE_PREFIX = get_secret("JWT_QUERY_STRING_VALUE_PREFIX", "secret/app/flask", "jwt_query_string_value_prefix") or "Bearer"
    JWT_COOKIE_NAME = get_secret("JWT_COOKIE_NAME", "secret/app/flask", "jwt_cookie_name") or "access_token"
    JWT_COOKIE_CSRF_PROTECT = get_secret("JWT_COOKIE_CSRF_PROTECT", "secret/app/flask", "jwt_cookie_csrf_protect").lower() == "true"
    JWT_COOKIE_SECURE = get_secret("JWT_COOKIE_SECURE", "secret/app/flask", "jwt_cookie_secure").lower() == "true"
    JWT_COOKIE_SAMESITE = get_secret("JWT_COOKIE_SAMESITE", "secret/app/flask", "jwt_cookie_samesite") or "Lax"
    JWT_COOKIE_DOMAIN = get_secret("JWT_COOKIE_DOMAIN", "secret/app/flask", "jwt_cookie_domain") or None
    JWT_COOKIE_PATH = get_secret("JWT_COOKIE_PATH", "secret/app/flask", "jwt_cookie_path") or "/"
    JWT_COOKIE_MAX_AGE = int(get_secret("JWT_COOKIE_MAX_AGE", "secret/app/flask", "jwt_cookie_max_age") or "3600")  # 1 hour in seconds

    # Toggle SSL for PostgreSQL
    USE_SSL = get_secret("USE_SSL", "secret/app/flask", "ssl").lower() in ("true", "1")

    # Database Pool Configuration
    DB_POOL_MIN_CONN = int(get_secret("DB_POOL_MIN_CONN", "secret/app/flask", "min_conn") or "1")
    DB_POOL_MAX_CONN = int(get_secret("DB_POOL_MAX_CONN", "secret/app/flask", "max_conn") or "10")
    
    # Connection Pool Security Settings
    DB_CONNECT_TIMEOUT = int(get_secret("DB_CONNECT_TIMEOUT", "secret/app/flask", "connect_timeout") or "10")  # Connection timeout in seconds
    DB_STATEMENT_TIMEOUT = int(get_secret("DB_STATEMENT_TIMEOUT", "secret/app/flask", "statement_timeout") or "30000")  # Statement timeout in milliseconds
    DB_KEEPALIVES = int(get_secret("DB_KEEPALIVES", "secret/app/flask", "keepalive") or "1")  # Enable keepalive
    DB_KEEPALIVES_IDLE = int(get_secret("DB_KEEPALIVES_IDLE", "secret/app/flask", "keepalive_idle") or "30")  # Idle timeout in seconds
    DB_KEEPALIVES_INTERVAL = int(get_secret("DB_KEEPALIVES_INTERVAL", "secret/app/flask", "keepalive_interval") or "10")  # Keepalive interval in seconds
    DB_KEEPALIVES_COUNT = int(get_secret("DB_KEEPALIVES_COUNT", "secret/app/flask", "keepalive_count") or "5")  # Maximum number of keepalive attempts
    DB_MAX_CONNECTIONS_PER_USER = int(get_secret("DB_MAX_CONNECTIONS_PER_USER", "secret/app/flask", "max_conn_per_user") or "5")  # Maximum connections per user
    
    # Resource Protection
    DB_MAX_QUERY_SIZE = int(get_secret("DB_MAX_QUERY_SIZE", "secret/app/flask", "max_query_size") or "10000")  # Maximum query size in bytes
    DB_MAX_RESULT_SIZE = int(get_secret("DB_MAX_RESULT_SIZE", "secret/app/flask", "max_result_size") or "1048576")  # Maximum result size in bytes (1MB)
    
    # Connection Retry Settings
    DB_RETRY_COUNT = int(get_secret("DB_RETRY_COUNT", "secret/app/flask", "retry_count") or "3")  # Number of connection retry attempts
    DB_RETRY_DELAY = int(get_secret("DB_RETRY_DELAY", "secret/app/flask", "retry_delay") or "1")  # Delay between retries in seconds
    
    # Flask-Limiter: Redis backend for rate limiting
    RATE_LIMIT_STORAGE_URL = get_secret("RATE_LIMIT_STORAGE_URL", "secret/app/flask", "rate_limit_storage_url") or "redis://localhost:6379/0"

    # Enable or disable logging
    LOGGING_ENABLED = get_secret("LOGGING_ENABLED", "secret/app/flask", "logging_enabled").lower() in ("true", "1")

    # Redis Security Settings
    REDIS_USE_SSL = get_secret("REDIS_USE_SSL", "secret/app/flask", "redis_ssl").lower() == "true"
    REDIS_SSL_VERIFY_MODE = get_secret("REDIS_SSL_VERIFY_MODE", "secret/app/flask", "redis_ssl_verify_mode") or "required"
    REDIS_MAX_CONNECTIONS = int(get_secret("REDIS_MAX_CONNECTIONS", "secret/app/flask", "redis_max_conn") or "10")
    REDIS_SOCKET_TIMEOUT = int(get_secret("REDIS_SOCKET_TIMEOUT", "secret/app/flask", "redis_socket_timeout") or "5")
    REDIS_SOCKET_CONNECT_TIMEOUT = int(get_secret("REDIS_SOCKET_CONNECT_TIMEOUT", "secret/app/flask", "redis_socket_connect_timeout") or "5")
    REDIS_RETRY_ON_TIMEOUT = get_secret("REDIS_RETRY_ON_TIMEOUT", "secret/app/flask", "redis_retry_on_timeout").lower() == "true"
    REDIS_MAX_RETRIES = int(get_secret("REDIS_MAX_RETRIES", "secret/app/flask", "redis_max_retries") or "3")
    REDIS_KEY_PREFIX = get_secret("REDIS_KEY_PREFIX", "secret/app/flask", "redis_key_prefix") or "app"
    REDIS_ENCRYPTION_KEY = get_secret("REDIS_ENCRYPTION_KEY", "secret/app/flask", "redis_encryption_key") or ""
    REDIS_ENCRYPTION_SALT = get_secret("REDIS_ENCRYPTION_SALT", "secret/app/flask", "redis_encryption_salt") or ""
    REDIS_ENCRYPTION_ITERATIONS = int(get_secret("REDIS_ENCRYPTION_ITERATIONS", "secret/app/flask", "redis_encryption_iterations") or "100000")
    REDIS_MAX_CACHE_SIZE = int(get_secret("REDIS_MAX_CACHE_SIZE", "secret/app/flask", "redis_max_cache_size") or "1048576")  # 1MB in bytes
    REDIS_CACHE_TTL = int(get_secret("REDIS_CACHE_TTL", "secret/app/flask", "redis_cache_ttl") or "300")  # 5 minutes in seconds

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED = get_secret("RATE_LIMIT_ENABLED", "secret/app/flask", "rate_limit_enabled").lower() == "true"
    RATE_LIMIT_IP_REQUESTS = int(get_secret("RATE_LIMIT_IP_REQUESTS", "secret/app/flask", "rate_limit_ip_requests") or "100")  # Requests per window
    RATE_LIMIT_IP_WINDOW = int(get_secret("RATE_LIMIT_IP_WINDOW", "secret/app/flask", "rate_limit_ip_window") or "60")  # Window in seconds
    RATE_LIMIT_IP_PREFIX = get_secret("RATE_LIMIT_IP_PREFIX", "secret/app/flask", "rate_limit_ip_prefix") or "rate_limit:ip"
    RATE_LIMIT_USER_REQUESTS = int(get_secret("RATE_LIMIT_USER_REQUESTS", "secret/app/flask", "rate_limit_user_requests") or "1000")  # Requests per window
    RATE_LIMIT_USER_WINDOW = int(get_secret("RATE_LIMIT_USER_WINDOW", "secret/app/flask", "rate_limit_user_window") or "3600")  # Window in seconds
    RATE_LIMIT_USER_PREFIX = get_secret("RATE_LIMIT_USER_PREFIX", "secret/app/flask", "rate_limit_user_prefix") or "rate_limit:user"
    RATE_LIMIT_API_KEY_REQUESTS = int(get_secret("RATE_LIMIT_API_KEY_REQUESTS", "secret/app/flask", "rate_limit_api_key_requests") or "10000")  # Requests per window
    RATE_LIMIT_API_KEY_WINDOW = int(get_secret("RATE_LIMIT_API_KEY_WINDOW", "secret/app/flask", "rate_limit_api_key_window") or "3600")  # Window in seconds
    RATE_LIMIT_API_KEY_PREFIX = get_secret("RATE_LIMIT_API_KEY_PREFIX", "secret/app/flask", "rate_limit_api_key_prefix") or "rate_limit:api_key"
    RATE_LIMIT_HEADERS_ENABLED = get_secret("RATE_LIMIT_HEADERS_ENABLED", "secret/app/flask", "rate_limit_headers_enabled").lower() == "true"
    RATE_LIMIT_HEADER_LIMIT = get_secret("RATE_LIMIT_HEADER_LIMIT", "secret/app/flask", "rate_limit_header_limit") or "X-RateLimit-Limit"
    RATE_LIMIT_HEADER_REMAINING = get_secret("RATE_LIMIT_HEADER_REMAINING", "secret/app/flask", "rate_limit_header_remaining") or "X-RateLimit-Remaining"
    RATE_LIMIT_HEADER_RESET = get_secret("RATE_LIMIT_HEADER_RESET", "secret/app/flask", "rate_limit_header_reset") or "X-RateLimit-Reset"

    # Auto-ban Configuration
    AUTO_BAN_ENABLED = get_secret("AUTO_BAN_ENABLED", "secret/app/flask", "auto_ban_enabled").lower() == "true"
    AUTO_BAN_VIOLATIONS_THRESHOLD = int(get_secret("AUTO_BAN_VIOLATIONS_THRESHOLD", "secret/app/flask", "auto_ban_violations_threshold") or "5")  # Number of violations before ban
    AUTO_BAN_DURATION = int(get_secret("AUTO_BAN_DURATION", "secret/app/flask", "auto_ban_duration") or "3600")  # Ban duration in seconds (default 1 hour)
    AUTO_BAN_WINDOW = int(get_secret("AUTO_BAN_WINDOW", "secret/app/flask", "auto_ban_window") or "300")  # Window to track violations (default 5 minutes)
    AUTO_BAN_PREFIX = get_secret("AUTO_BAN_PREFIX", "secret/app/flask", "auto_ban_prefix") or "ban"
    AUTO_BAN_VIOLATIONS_PREFIX = get_secret("AUTO_BAN_VIOLATIONS_PREFIX", "secret/app/flask", "auto_ban_violations_prefix") or "violations"

    # WebSocket Configuration
    WS_MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB default max message size
    WS_MAX_TEXT_MESSAGE_SIZE = 1024 * 1024  # 1MB for text messages
    WS_MAX_BINARY_MESSAGE_SIZE = 5 * 1024 * 1024  # 5MB for binary messages
    WS_MAX_JSON_MESSAGE_SIZE = 512 * 1024  # 512KB for JSON messages
    WS_MESSAGE_RATE_LIMIT = 100  # messages per second per user
    WS_MESSAGE_RATE_WINDOW = 1  # seconds for rate limiting
    WS_COMPRESSION_THRESHOLD = 1024  # 1KB - compress messages larger than this
    WS_COMPRESSION_LEVEL = 6  # zlib compression level (1-9)
    WS_MAX_PAYLOAD_SIZE = 1024 * 1024  # 1MB max payload size
    WS_PING_TIMEOUT = 60
    WS_PING_INTERVAL = 25
    WS_RATE_LIMIT_CONNECTIONS = 100
    WS_RATE_LIMIT_MESSAGES = 1000
    WS_RATE_LIMIT_WINDOW = 3600  # 1 hour
    WS_SESSION_TTL = 3600  # 1 hour
    WS_ROOM_SIZE_LIMIT = 2
    WS_ROOM_SIZE_CHECK_INTERVAL = 300  # 5 minutes
    WS_ALLOWED_ORIGINS = get_secret("WS_ALLOWED_ORIGINS", "secret/app/flask", "allowed_origins").split(",") or ['http://localhost:5000', 'http://localhost:3000']

    # Presence Tracking Configuration
    WS_PRESENCE_CHECK_INTERVAL = 30  # seconds between presence checks
    WS_PRESENCE_TIMEOUT = 90  # seconds before marking user as offline
    WS_PRESENCE_CLEANUP_INTERVAL = 300  # seconds between cleanup operations
    WS_PRESENCE_STATUSES = {
        'online': 'online',
        'away': 'away',
        'offline': 'offline',
        'busy': 'busy'
    }

    # Message Size Limits
    WS_MAX_MESSAGE_LENGTH = 1000  # Maximum length for text messages
    WS_MAX_BINARY_SIZE = 5 * 1024 * 1024  # 5MB for binary data
    WS_MAX_JSON_DEPTH = 10  # Maximum nesting depth for JSON messages
    WS_MAX_JSON_SIZE = 1024 * 1024  # 1MB for JSON messages
    WS_MAX_ARRAY_SIZE = 1000  # Maximum number of elements in arrays
    WS_MAX_OBJECT_SIZE = 100  # Maximum number of properties in objects

    # Credit Amount Validation Settings
    CREDIT_MIN_AMOUNT = float(get_secret("CREDIT_MIN_AMOUNT", "secret/app/flask", "credit_min_amount") or "0.01")  # Minimum credit amount
    CREDIT_MAX_AMOUNT = float(get_secret("CREDIT_MAX_AMOUNT", "secret/app/flask", "credit_max_amount") or "1000000.0")  # Maximum credit amount
    CREDIT_PRECISION = int(get_secret("CREDIT_PRECISION", "secret/app/flask", "credit_precision") or "2")  # Number of decimal places allowed
    CREDIT_ALLOW_NEGATIVE = get_secret("CREDIT_ALLOW_NEGATIVE", "secret/app/flask", "credit_allow_negative").lower() == "true"  # Whether negative amounts are allowed

    # Transaction Validation Settings
    MAX_METADATA_SIZE = int(get_secret("MAX_METADATA_SIZE", "secret/app/flask", "max_metadata_size") or "1024")  # Maximum metadata size in bytes
    MAX_REFERENCE_ID_LENGTH = int(get_secret("MAX_REFERENCE_ID_LENGTH", "secret/app/flask", "max_reference_id_length") or "64")  # Maximum reference ID length
    ALLOWED_TRANSACTION_TYPES = get_secret("ALLOWED_TRANSACTION_TYPES", "secret/app/flask", "allowed_transaction_types").split(",") or "purchase,reward,burn,transfer,refund"

    # Transaction Integrity Settings
    TRANSACTION_WINDOW = int(get_secret("TRANSACTION_WINDOW", "secret/app/flask", "transaction_window") or "3600")  # Time window for replay attack prevention (in seconds)
    REQUIRE_TRANSACTION_ID = get_secret("REQUIRE_TRANSACTION_ID", "secret/app/flask", "require_transaction_id").lower() == "true"  # Whether transaction IDs are required
    ENFORCE_BALANCE_VALIDATION = get_secret("ENFORCE_BALANCE_VALIDATION", "secret/app/flask", "enforce_balance_validation").lower() == "true"  # Whether to enforce balance validation

    # Payload Validation Settings
    MAX_PAYLOAD_SIZE = int(get_secret("MAX_PAYLOAD_SIZE", "secret/app/flask", "max_payload_size") or "1048576")  # 1MB default
    MAX_NESTING_DEPTH = int(get_secret("MAX_NESTING_DEPTH", "secret/app/flask", "max_nesting_depth") or "10")  # Maximum nesting depth
    MAX_ARRAY_SIZE = int(get_secret("MAX_ARRAY_SIZE", "secret/app/flask", "max_array_size") or "1000")  # Maximum array size
    MAX_STRING_LENGTH = int(get_secret("MAX_STRING_LENGTH", "secret/app/flask", "max_string_length") or "65536")  # Maximum string length

    # Encryption settings
    ENCRYPTION_SALT = get_secret("ENCRYPTION_SALT", "secret/app/flask", "encryption_salt") or "default_salt_123"  # Should be changed in production
    SENSITIVE_FIELDS = [
        "user_id",
        "email",
        "phone",
        "address",
        "credit_balance",
        "transaction_history"
    ]

    # MongoDB Configuration
    MONGODB_AUTH_SOURCE = get_secret("MONGODB_AUTH_SOURCE", "secret/app/flask", "mongodb_auth_source") or "admin"
    
    # MongoDB Role-Based Access Control
    MONGODB_ROLES = {
        "admin": ["readWriteAnyDatabase", "dbAdminAnyDatabase", "userAdminAnyDatabase"],
        "read_write": ["readWrite"],
        "read_only": ["read"]
    }
    
    # MongoDB Replica Set Configuration
    MONGODB_REPLICA_SET = get_secret("MONGODB_REPLICA_SET", "secret/app/flask", "mongodb_replica_set") or ""
    MONGODB_READ_PREFERENCE = get_secret("MONGODB_READ_PREFERENCE", "secret/app/flask", "mongodb_read_preference") or "primary"
    MONGODB_READ_CONCERN = get_secret("MONGODB_READ_CONCERN", "secret/app/flask", "mongodb_read_concern") or "majority"
    MONGODB_WRITE_CONCERN = get_secret("MONGODB_WRITE_CONCERN", "secret/app/flask", "mongodb_write_concern") or "majority"
    
    # MongoDB Connection Settings
    MONGODB_MAX_POOL_SIZE = int(get_secret("MONGODB_MAX_POOL_SIZE", "secret/app/flask", "mongodb_max_pool_size") or "100")
    MONGODB_MIN_POOL_SIZE = int(get_secret("MONGODB_MIN_POOL_SIZE", "secret/app/flask", "mongodb_min_pool_size") or "10")
    MONGODB_MAX_IDLE_TIME_MS = int(get_secret("MONGODB_MAX_IDLE_TIME_MS", "secret/app/flask", "mongodb_max_idle_time_ms") or "60000")
    MONGODB_SOCKET_TIMEOUT_MS = int(get_secret("MONGODB_SOCKET_TIMEOUT_MS", "secret/app/flask", "mongodb_socket_timeout_ms") or "5000")
    MONGODB_CONNECT_TIMEOUT_MS = int(get_secret("MONGODB_CONNECT_TIMEOUT_MS", "secret/app/flask", "mongodb_connect_timeout_ms") or "5000")
    
    # MongoDB SSL/TLS Settings
    MONGODB_SSL = get_secret("MONGODB_SSL", "secret/app/flask", "mongodb_ssl").lower() == "true"
    MONGODB_SSL_CA_FILE = get_secret("MONGODB_SSL_CA_FILE", "secret/app/flask", "mongodb_ssl_ca_file") or ""
    MONGODB_SSL_CERT_FILE = get_secret("MONGODB_SSL_CERT_FILE", "secret/app/flask", "mongodb_ssl_cert_file") or ""
    MONGODB_SSL_KEY_FILE = get_secret("MONGODB_SSL_KEY_FILE", "secret/app/flask", "mongodb_ssl_key_file") or ""
    MONGODB_SSL_ALLOW_INVALID_CERTIFICATES = get_secret("MONGODB_SSL_ALLOW_INVALID_CERTIFICATES", "secret/app/flask", "mongodb_ssl_allow_invalid_certificates").lower() == "true"
