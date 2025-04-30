# WebSocket Validators Documentation

## Overview
The WebSocket Validators provide comprehensive validation and sanitization for WebSocket communications. They ensure data integrity, security, and proper formatting for messages, room IDs, user data, and event payloads.

## Core Components

### WebSocketValidator
The WebSocketValidator class manages all validation and sanitization operations.

#### Class Definition
```python
class WebSocketValidator:
    """Validates WebSocket inputs and sanitizes data."""
```

#### Dependencies
- Custom logging utilities
- Config
- Regular expressions
- JSON handling
- Compression utilities

#### Core Features

##### Message Validation
- `validate_message(data: Dict[str, Any]) -> Optional[str]`
  - Validates message content
  - Checks message type
  - Validates message length
  - Sanitizes content
  - Returns error message if invalid

- `validate_binary_data(data: bytes) -> Optional[str]`
  - Validates binary data
  - Checks data type
  - Validates data size
  - Returns error message if invalid

- `validate_json_data(data: Dict[str, Any]) -> Optional[str]`
  - Validates JSON structure
  - Checks nesting depth
  - Validates array sizes
  - Validates object sizes
  - Returns error message if invalid

##### Room Validation
- `validate_room_id(room_id: str) -> Optional[str]`
  - Validates room ID
  - Checks ID format
  - Validates length
  - Checks character set
  - Returns error message if invalid

##### User Data Validation
- `validate_user_data(user_data: Dict[str, Any]) -> Optional[str]`
  - Validates user information
  - Checks required fields
  - Validates username
  - Validates email
  - Validates user ID
  - Returns error message if invalid

##### Event Payload Validation
- `validate_event_payload(event: str, data: Dict[str, Any]) -> Optional[str]`
  - Validates event-specific data
  - Supports multiple event types
  - Returns error message if invalid

##### Message Sanitization
- `sanitize_message(message: str) -> str`
  - Removes HTML tags
  - Removes script tags
  - Removes dangerous attributes
  - Returns sanitized message

- `sanitize_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]`
  - Sanitizes username
  - Sanitizes email
  - Returns sanitized data

##### Message Size Validation
- `validate_message_size(message: str) -> Optional[str]`
  - Validates general message size
  - Returns error message if invalid

- `validate_text_message_size(message: str) -> Optional[str]`
  - Validates text message size
  - Returns error message if invalid

- `validate_binary_message_size(message: bytes) -> Optional[str]`
  - Validates binary message size
  - Returns error message if invalid

- `validate_json_message_size(message: str) -> Optional[str]`
  - Validates JSON message size
  - Returns error message if invalid

##### Rate Limiting
- `validate_message_rate(session_id: str) -> Optional[str]`
  - Validates message rate
  - Returns error message if rate exceeded

##### Message Compression
- `should_compress_message(message: Union[str, bytes]) -> bool`
  - Determines if compression needed
  - Returns compression decision

- `compress_message(message: Union[str, bytes]) -> bytes`
  - Compresses message
  - Returns compressed data

- `decompress_message(compressed_message: bytes) -> bytes`
  - Decompresses message
  - Returns original data

## Configuration

### Validation Limits
- `MAX_MESSAGE_LENGTH`: 1000 characters
- `MAX_ROOM_ID_LENGTH`: 50 characters
- `MAX_USERNAME_LENGTH`: 50 characters
- `WS_MAX_MESSAGE_LENGTH`: Configurable
- `WS_MAX_BINARY_SIZE`: Configurable
- `WS_MAX_JSON_SIZE`: Configurable
- `WS_MAX_JSON_DEPTH`: Configurable
- `WS_MAX_ARRAY_SIZE`: Configurable
- `WS_MAX_OBJECT_SIZE`: Configurable

### Character Patterns
- `ALLOWED_ROOM_ID_CHARS`: `^[a-zA-Z0-9_-]+$`
- `ALLOWED_USERNAME_CHARS`: `^[a-zA-Z0-9_-]+$`

## Usage Example
```python
# Initialize validator
validator = WebSocketValidator()

# Validate message
message_data = {
    "message": "Hello, world!"
}
error = validator.validate_message(message_data)
if error:
    print(f"Validation error: {error}")

# Validate room ID
room_id = "game_room_123"
error = validator.validate_room_id(room_id)
if error:
    print(f"Validation error: {error}")

# Validate user data
user_data = {
    "id": 1,
    "username": "player1",
    "email": "player1@example.com"
}
error = validator.validate_user_data(user_data)
if error:
    print(f"Validation error: {error}")

# Sanitize message
message = "<script>alert('xss')</script>Hello"
sanitized = validator.sanitize_message(message)
print(f"Sanitized message: {sanitized}")
```

## Error Handling
- Validates input types
- Checks data formats
- Verifies size limits
- Handles invalid data
- Implements proper recovery

## Security Considerations
- Sanitizes HTML content
- Removes script tags
- Validates input formats
- Checks data sizes
- Implements rate limiting
- Handles compression

## Best Practices
1. Validate all inputs
2. Sanitize user data
3. Check message sizes
4. Implement rate limiting
5. Use compression when needed
6. Handle errors properly
7. Follow security guidelines
8. Test all scenarios
9. Monitor validation failures
10. Implement proper logging 