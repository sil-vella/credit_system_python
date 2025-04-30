# Secret Manager Documentation

## Overview
The Secret Manager provides secure handling of sensitive information such as API keys, passwords, and encryption keys. It reads secrets from files specified by environment variables, ensuring secure storage and access to sensitive data.

## Core Components

### Secret Manager Functions
The Secret Manager consists of utility functions for managing secrets.

#### Dependencies
- os module
- File system access

#### Core Features

##### Secret Reading
- `read_secret_file(file_path)`
  - Reads secret from file
  - Handles file access
  - Strips whitespace
  - Returns secret value
  - Raises errors for:
    - File not found
    - Permission denied

##### Secret Management
- `get_secrets()`
  - Gets all required secrets
  - Reads from environment
  - Validates file paths
  - Returns secrets dict
  - Raises errors for:
    - Missing environment variables
    - File access issues

## Configuration

### Required Environment Variables
- `APP_SECRET_KEY_FILE`: Path to app secret key
- `JWT_SECRET_KEY_FILE`: Path to JWT secret key
- `ENCRYPTION_KEY_FILE`: Path to encryption key
- `POSTGRES_PASSWORD_FILE`: Path to PostgreSQL password

### Secret File Format
- Plain text files
- One secret per file
- No trailing whitespace
- Proper file permissions

## Usage Example
```python
# Get all secrets
secrets = get_secrets()

# Access specific secret
app_secret = secrets['APP_SECRET_KEY']
jwt_secret = secrets['JWT_SECRET_KEY']

# Read single secret
encryption_key = read_secret_file('/path/to/encryption.key')
```

## Error Handling
- Validates file existence
- Checks permissions
- Verifies environment variables
- Implements proper error messages

## Security Considerations
- Uses file-based storage
- Requires proper permissions
- Validates file access
- Protects sensitive data
- Follows security best practices

## Best Practices
1. Store secrets in files
2. Set proper permissions
3. Use environment variables
4. Handle errors properly
5. Follow security guidelines
6. Test file access
7. Monitor file changes
8. Implement proper logging
9. Document secret locations
10. Regular security audits 