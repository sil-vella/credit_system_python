# Redis Manager Documentation

## Overview
The Redis Manager provides a secure and efficient interface for Redis operations with built-in encryption, connection pooling, and error handling. It implements the Singleton pattern and includes features for data encryption, secure key generation, and token management.

## Core Components

### RedisManager
The RedisManager class manages all Redis-related operations.

#### Class Definition
```python
class RedisManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Initialization code
```

#### Dependencies
- Redis
- Cryptography
- Config
- Custom logging utilities

#### Core Features

##### Connection Management
- `_initialize_connection_pool()`
  - Initializes Redis connection
  - Configures connection pool
  - Sets up SSL if enabled
  - Implements error handling

- `_ensure_connection()`
  - Ensures active connection
  - Handles reconnection
  - Manages connection state

- `dispose()`
  - Cleans up connections
  - Closes connection pool
  - Handles cleanup errors

##### Data Encryption
- `_setup_encryption()`
  - Sets up encryption key
  - Uses PBKDF2 for key derivation
  - Configures cipher suite

- `_encrypt_data(data)`
  - Encrypts data
  - Handles serialization
  - Manages data types

- `_decrypt_data(encrypted_data)`
  - Decrypts data
  - Handles deserialization
  - Manages data types

##### Key Management
- `_generate_secure_key(prefix, *args)`
  - Generates secure keys
  - Uses SHA-256 hashing
  - Implements key prefixing

##### Basic Operations
- `get(key, *args)`
  - Retrieves value
  - Handles decryption
  - Returns formatted data

- `set(key, value, expire=None, *args)`
  - Stores value
  - Handles encryption
  - Manages expiration

- `delete(key, *args)`
  - Deletes value
  - Handles cleanup
  - Returns operation status

##### Advanced Operations
- `exists(key, *args)`
  - Checks key existence
  - Returns boolean result

- `expire(key, seconds, *args)`
  - Sets expiration
  - Returns operation status

- `ttl(key, *args)`
  - Gets time to live
  - Returns TTL value

- `incr(key, *args)`
  - Increments value
  - Returns new value

- `decr(key, *args)`
  - Decrements value
  - Returns new value

##### Hash Operations
- `hset(key, field, value, *args)`
  - Sets hash field
  - Handles encryption
  - Returns operation status

- `hget(key, field, *args)`
  - Gets hash field
  - Handles decryption
  - Returns field value

- `hdel(key, field, *args)`
  - Deletes hash field
  - Returns operation status

- `hgetall(key, *args)`
  - Gets all hash fields
  - Returns complete hash

##### List Operations
- `lpush(key, value, *args)`
  - Pushes to list head
  - Returns list length

- `rpush(key, value, *args)`
  - Pushes to list tail
  - Returns list length

- `lpop(key, *args)`
  - Pops from list head
  - Returns popped value

- `rpop(key, *args)`
  - Pops from list tail
  - Returns popped value

- `lrange(key, start, end, *args)`
  - Gets list range
  - Returns range values

##### Room Management
- `set_room_size(room_id: str, size: int, expire: int = 3600) -> bool`
  - Sets room size
  - Manages expiration
  - Returns operation status

- `get_room_size(room_id: str) -> int`
  - Gets room size
  - Returns size value

- `update_room_size(room_id: str, delta: int)`
  - Updates room size
  - Handles increments
  - Manages cleanup

- `check_and_increment_room_size(room_id: str, room_size_limit: int = 100) -> bool`
  - Checks room size
  - Handles increments
  - Returns operation status

##### Token Management
- `store_token(token_type: str, token: str, expire: int = 1800) -> bool`
  - Stores token
  - Manages expiration
  - Returns operation status

- `is_token_valid(token_type: str, token: str) -> bool`
  - Validates token
  - Returns validation result

- `revoke_token(token_type: str, token: str) -> bool`
  - Revokes token
  - Returns operation status

- `cleanup_expired_tokens(token_type: str) -> bool`
  - Cleans up tokens
  - Returns operation status

## Configuration

### Connection Settings
- `REDIS_URL`: Connection URL
- `REDIS_HOST`: Host address
- `REDIS_PORT`: Port number
- `REDIS_PASSWORD`: Password
- `REDIS_USE_SSL`: SSL flag
- `REDIS_SSL_VERIFY_MODE`: SSL verification

### Security Settings
- Encryption key derivation
- Token expiration
- Secure key generation

## Usage Example
```python
# Initialize Redis manager
redis_manager = RedisManager()

# Store data
redis_manager.set(
    "user:session",
    {"user_id": 1, "roles": ["admin"]},
    expire=3600
)

# Retrieve data
session_data = redis_manager.get("user:session")

# Store token
redis_manager.store_token(
    "access",
    "token123",
    expire=1800
)

# Check token
is_valid = redis_manager.is_token_valid("access", "token123")

# Manage room size
redis_manager.set_room_size("room123", 5)
current_size = redis_manager.get_room_size("room123")
```

## Error Handling
- Validates connections
- Handles encryption errors
- Manages operation failures
- Implements proper recovery

## Security Considerations
- Implements encryption
- Uses secure key generation
- Manages token security
- Handles sensitive data
- Implements proper access control

## Best Practices
1. Use proper connection management
2. Handle encryption carefully
3. Implement proper error handling
4. Manage token lifecycle
5. Follow security guidelines
6. Test all scenarios
7. Monitor performance
8. Clean up resources
9. Handle data types properly
10. Implement proper logging 