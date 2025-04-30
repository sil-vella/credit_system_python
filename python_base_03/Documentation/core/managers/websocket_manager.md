# WebSocket Manager Documentation

## Overview
The WebSocket Manager provides comprehensive WebSocket functionality for real-time communication in the application. It handles connection management, room management, session handling, and message broadcasting with built-in security features and rate limiting.

## Core Components

### WebSocketManager
The WebSocketManager class manages all WebSocket-related operations.

#### Class Definition
```python
class WebSocketManager:
    def __init__(self):
        # Initialization code
```

#### Dependencies
- Flask-SocketIO
- RedisManager
- WebSocketValidator
- Config
- Custom logging utilities

#### Core Features

##### Connection Management
- `initialize(app)`
  - Initializes WebSocket server
  - Sets up event handlers
  - Configures CORS
  - Implements connection handling

- `handle_connect()`
  - Handles new connections
  - Validates origin
  - Checks rate limits
  - Manages session data

- `handle_disconnect()`
  - Handles disconnections
  - Cleans up session data
  - Updates room memberships
  - Manages presence status

##### Session Management
- `store_session_data(session_id: str, session_data: Dict[str, Any])`
  - Stores session data in Redis
  - Handles data serialization
  - Manages data expiration
  - Implements error handling

- `get_session_data(session_id: str) -> Optional[Dict[str, Any]]`
  - Retrieves session data
  - Handles data deserialization
  - Manages data types
  - Returns formatted data

- `cleanup_session_data(session_id: str)`
  - Removes session data
  - Cleans up Redis entries
  - Handles cleanup errors

##### Room Management
- `create_room(room_id: str, permission: str = "public", owner_id: Optional[int] = None, allowed_users: Optional[Set[int]] = None, allowed_roles: Optional[Set[str]] = None) -> bool`
  - Creates new room
  - Sets permissions
  - Manages access control
  - Returns creation status

- `join_room(room_id: str, session_id: str, user_id: Optional[str] = None, user_roles: Optional[Set[str]] = None) -> bool`
  - Joins room
  - Validates access
  - Updates memberships
  - Returns join status

- `leave_room(room_id: str, session_id: str)`
  - Leaves room
  - Updates memberships
  - Cleans up data
  - Handles errors

##### Message Broadcasting
- `broadcast_to_room(room_id: str, event: str, data: Dict[str, Any])`
  - Broadcasts to room
  - Handles errors
  - Manages delivery

- `broadcast_to_all(event: str, data: Dict[str, Any])`
  - Broadcasts to all
  - Handles errors
  - Manages delivery

- `send_to_session(session_id: str, event: str, data: Any)`
  - Sends to session
  - Handles errors
  - Manages delivery

##### Security Features
- `validate_origin(origin: str) -> bool`
  - Validates origin
  - Checks CORS
  - Returns validation result

- `check_rate_limit(client_id: str, limit_type: str) -> bool`
  - Checks rate limits
  - Manages counters
  - Returns limit status

- `requires_auth(handler: Callable) -> Callable`
  - Decorator for auth
  - Validates tokens
  - Handles errors

##### Presence Management
- `update_user_presence(session_id: str, status: str = 'online')`
  - Updates presence
  - Manages status
  - Handles cleanup

- `get_user_presence(user_id: str) -> Optional[Dict[str, Any]]`
  - Gets presence
  - Returns status
  - Handles errors

- `get_room_presence(room_id: str) -> List[Dict[str, Any]]`
  - Gets room presence
  - Returns members
  - Handles errors

## Configuration

### Rate Limits
- `WS_RATE_LIMIT_CONNECTIONS`: Max connections
- `WS_RATE_LIMIT_MESSAGES`: Max messages
- `WS_RATE_LIMIT_WINDOW`: Time window

### Room Settings
- `WS_ROOM_SIZE_LIMIT`: Max room size
- `WS_ROOM_SIZE_CHECK_INTERVAL`: Check interval

### Presence Settings
- `WS_PRESENCE_CHECK_INTERVAL`: Check interval
- `WS_PRESENCE_TIMEOUT`: Timeout duration
- `WS_PRESENCE_CLEANUP_INTERVAL`: Cleanup interval

## Usage Example
```python
# Initialize WebSocket manager
ws_manager = WebSocketManager()

# Initialize with Flask app
ws_manager.initialize(app)

# Create room
ws_manager.create_room(
    room_id="game123",
    permission="private",
    owner_id=1,
    allowed_users={1, 2, 3}
)

# Join room
ws_manager.join_room(
    room_id="game123",
    session_id="session1",
    user_id="user1",
    user_roles={"player"}
)

# Broadcast message
ws_manager.broadcast_to_room(
    room_id="game123",
    event="game_update",
    data={"status": "playing"}
)

# Send to session
ws_manager.send_to_session(
    session_id="session1",
    event="private_message",
    data={"message": "Hello"}
)
```

## Error Handling
- Validates connections
- Handles disconnections
- Manages room errors
- Implements proper recovery

## Security Considerations
- Implements CORS
- Manages rate limits
- Handles authentication
- Controls room access
- Protects sensitive data

## Best Practices
1. Use proper room management
2. Handle connections carefully
3. Implement rate limiting
4. Manage presence properly
5. Handle errors gracefully
6. Follow security guidelines
7. Test all scenarios
8. Monitor performance
9. Clean up resources
10. Implement proper logging 