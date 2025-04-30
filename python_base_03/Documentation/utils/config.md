# Configuration Module Documentation

## Overview
The Configuration module provides centralized configuration management for the application. It handles environment variables, security settings, and various service configurations. The module uses environment variables with sensible defaults and implements security best practices.

## Core Components

### Config Class
The main configuration class that manages all application settings.

#### Class Definition
```python
class Config:
    # Configuration settings
```

#### Configuration Categories

##### Application Settings
- Debug mode
- Application URL
- Logging settings

##### JWT Configuration
- Secret key
- Token expiration times
- Algorithm settings
- Header configuration
- Cookie settings
- CSRF protection
- Security options

##### Database Configuration
- Connection pool settings
- Security parameters
- Timeout values
- Keepalive settings
- Resource limits
- Retry configuration

##### Redis Configuration
- SSL settings
- Connection parameters
- Timeout values
- Retry settings
- Encryption options
- Cache configuration

##### WebSocket Configuration
- Message size limits
- Rate limiting
- Compression settings
- Session management
- Room settings
- Presence tracking

## Configuration Details

### JWT Settings
```python
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days
```

### Database Settings
```python
DB_POOL_MIN_CONN = 1
DB_POOL_MAX_CONN = 10
DB_CONNECT_TIMEOUT = 10
DB_STATEMENT_TIMEOUT = 30000
```

### Redis Settings
```python
REDIS_MAX_CONNECTIONS = 10
REDIS_SOCKET_TIMEOUT = 5
REDIS_MAX_CACHE_SIZE = 1048576  # 1MB
REDIS_CACHE_TTL = 300  # 5 minutes
```

### WebSocket Settings
```python
WS_MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
WS_MESSAGE_RATE_LIMIT = 100
WS_PING_TIMEOUT = 60
WS_ROOM_SIZE_LIMIT = 2
```

## Usage Example
```python
from utils.config.config import Config

# Access configuration values
debug_mode = Config.DEBUG
jwt_secret = Config.JWT_SECRET_KEY
db_pool_size = Config.DB_POOL_MAX_CONN
ws_message_limit = Config.WS_MESSAGE_RATE_LIMIT
```

## Environment Variables
All configuration values can be overridden using environment variables:
- `FLASK_DEBUG`
- `JWT_SECRET_KEY`
- `DB_POOL_MAX_CONN`
- `REDIS_MAX_CONNECTIONS`
- `WS_MESSAGE_RATE_LIMIT`

## Security Considerations
- Sensitive values use environment variables
- Default values are secure
- SSL/TLS settings
- Rate limiting
- Resource limits
- Timeout values
- Encryption options

## Best Practices
1. Use environment variables for sensitive data
2. Set appropriate timeouts
3. Configure rate limits
4. Enable SSL where possible
5. Set resource limits
6. Use secure defaults
7. Regular security reviews
8. Monitor configuration
9. Document changes
10. Test configurations 