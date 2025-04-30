# Logging Module Documentation

## Overview
The Logging module provides comprehensive logging functionality for the application. It includes custom formatters, multiple log types, and function call logging. The module supports different log levels, sanitization, and structured logging.

## Core Components

### Custom Formatters
- `CustomFormatter`: Formats logs with timestamps, levels, and file information
- `SimpleFormatter`: Provides basic timestamp and message formatting

### Log Types
- `custom_log`: General application logging
- `game_play_log`: Game-specific event logging
- `function_log`: Function call and execution logging

### Core Features

##### Log Sanitization
- `sanitize_log_message(message)`
  - Ensures UTF-8 encoding
  - Removes non-ASCII characters
  - Handles emoji removal
  - Manages encoding errors

##### Function Logging
- `log_function_call(func)`
  - Decorator for function logging
  - Tracks function entry/exit
  - Logs arguments and results
  - Manages variable changes

##### Plugin Logging
- `add_logging_to_plugin(plugin, exclude_instances, exclude_packages)`
  - Adds logging to plugin functions
  - Manages exclusions
  - Handles class methods
  - Controls logging scope

## Configuration

### Log Files
- `server.log`: General application logs
- `game_play.log`: Game-specific events
- `function.log`: Function execution details

### Log Settings
- Custom logging enabled
- Gameplay logging enabled
- Function logging enabled
- Log levels
- File handlers
- Formatters

## Usage Example
```python
# Basic logging
custom_log("Application started")

# Game play logging
game_play_log("Player joined game", action="join")

# Function logging
@log_function_call
def example_function(arg1, arg2):
    return arg1 + arg2

# Plugin logging
add_logging_to_plugin(
    MyPlugin,
    exclude_instances=[SomeClass],
    exclude_packages=["external"]
)
```

## Log Format
### Custom Format
```
[timestamp] - logger_name - level - message (filename:line_number)
```

### Simple Format
```
timestamp - message
```

## Log Levels
- DEBUG: Detailed information
- INFO: General information
- WARNING: Warning messages
- ERROR: Error conditions
- CRITICAL: Critical issues

## Security Considerations
- Message sanitization
- Encoding handling
- Sensitive data
- Log file access
- Information leakage
- Error handling

## Best Practices
1. Use appropriate log levels
2. Sanitize log messages
3. Handle encoding properly
4. Manage log file size
5. Regular log rotation
6. Monitor log levels
7. Secure log access
8. Regular cleanup
9. Test logging
10. Document changes 