# JWT Manager Documentation

## Overview
The JWT Manager provides comprehensive JSON Web Token (JWT) management with support for different token types, token binding, and revocation capabilities. It implements secure token creation, verification, and refresh mechanisms with Redis-based token storage.

## Core Components

### TokenType Enum
```python
class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    WEBSOCKET = "websocket"
```

### JWTManager
The JWTManager class manages all JWT-related operations.

#### Class Definition
```python
class JWTManager:
    def __init__(self):
        # Initialization code
```

#### Dependencies
- PyJWT
- RedisManager
- Config
- Custom logging utilities

#### Core Features

##### Token Creation
- `create_token(data: Dict[str, Any], token_type: TokenType, expires_in: Optional[int] = None) -> str`
  - Creates new token
  - Sets expiration
  - Adds client binding
  - Stores in Redis
  - Returns token string

- `create_access_token(data: Dict[str, Any], expires_in: Optional[int] = None) -> str`
  - Creates access token
  - Sets 30-minute expiration
  - Returns token string

- `create_refresh_token(data: Dict[str, Any], expires_in: Optional[int] = None) -> str`
  - Creates refresh token
  - Sets 24-hour expiration
  - Returns token string

- `create_websocket_token(data: Dict[str, Any], expires_in: Optional[int] = None) -> str`
  - Creates WebSocket token
  - Sets 30-minute expiration
  - Returns token string

##### Token Verification
- `verify_token(token: str, expected_type: Optional[TokenType] = None) -> Optional[Dict[str, Any]]`
  - Verifies token
  - Checks revocation
  - Validates type
  - Verifies client binding
  - Returns payload

- `verify_websocket_token(token: str) -> Optional[Dict[str, Any]]`
  - Verifies WebSocket token
  - Returns payload

##### Token Management
- `revoke_token(token: str) -> bool`
  - Revokes token
  - Removes from Redis
  - Returns operation status

- `refresh_token(refresh_token: str) -> Optional[str]`
  - Creates new access token
  - Uses refresh token
  - Returns new token

- `cleanup_expired_tokens()`
  - Cleans up expired tokens
  - Removes from Redis
  - Handles cleanup errors

##### Client Binding
- `_get_client_fingerprint() -> str`
  - Generates fingerprint
  - Uses IP and User-Agent
  - Returns fingerprint string

##### Token Storage
- `_store_token(token: str, expire: datetime, token_type: TokenType)`
  - Stores token in Redis
  - Sets expiration
  - Handles storage errors

- `_is_token_revoked(token: str) -> bool`
  - Checks token revocation
  - Returns revocation status

## Configuration

### Token Settings
- `JWT_SECRET_KEY`: Secret key
- `JWT_ALGORITHM`: Algorithm
- `access_token_expire_seconds`: 1800 (30 minutes)
- `refresh_token_expire_seconds`: 86400 (24 hours)
- `websocket_token_expire_seconds`: 1800 (30 minutes)

## Usage Example
```python
# Initialize JWT manager
jwt_manager = JWTManager()

# Create access token
access_token = jwt_manager.create_access_token({
    "user_id": 1,
    "roles": ["admin"]
})

# Create refresh token
refresh_token = jwt_manager.create_refresh_token({
    "user_id": 1
})

# Verify token
payload = jwt_manager.verify_token(access_token, TokenType.ACCESS)
if payload:
    print(f"User ID: {payload['user_id']}")

# Refresh token
new_access_token = jwt_manager.refresh_token(refresh_token)

# Create WebSocket token
ws_token = jwt_manager.create_websocket_token({
    "user_id": 1,
    "session_id": "session123"
})

# Verify WebSocket token
ws_payload = jwt_manager.verify_websocket_token(ws_token)
```

## Error Handling
- Handles invalid tokens
- Manages expired tokens
- Handles signature errors
- Implements proper recovery

## Security Considerations
- Implements token binding
- Manages token revocation
- Handles token expiration
- Protects sensitive data
- Implements proper access control

## Best Practices
1. Use proper token types
2. Handle token expiration
3. Implement token binding
4. Manage token revocation
5. Follow security guidelines
6. Test all scenarios
7. Monitor token usage
8. Clean up expired tokens
9. Handle errors properly
10. Implement proper logging 