# App Manager Documentation

## Overview
The App Manager serves as the central coordinator for the application, managing initialization, plugin registration, template handling, and hook management. It provides a unified interface for accessing various managers and coordinating their operations.

## Core Components

### AppManager
The AppManager class manages all application-level operations.

#### Class Definition
```python
class AppManager:
    def __init__(self):
        # Initialization code
```

#### Dependencies
- PluginManager
- ServicesManager
- HooksManager
- ModuleManager
- WebSocketManager
- Flask
- Jinja2
- Custom logging utilities

#### Core Features

##### Initialization
- `initialize(app)`
  - Initializes Flask app
  - Sets up services
  - Configures WebSocket
  - Registers plugins
  - Updates template loader
  - Handles errors

- `run(app, **kwargs)`
  - Runs Flask application
  - Supports WebSocket
  - Handles configuration

##### Plugin Management
- `get_plugins_path(return_url=False)`
  - Gets plugins directory
  - Supports URL path
  - Handles errors
  - Returns path string

##### Template Management
- `register_template_dir(template_dir)`
  - Registers template directory
  - Updates Jinja loader
  - Handles duplicates
  - Logs operations

- `_update_jinja_loader()`
  - Updates template loader
  - Combines loaders
  - Handles errors
  - Logs changes

##### Hook Management
- `register_hook(hook_name)`
  - Registers new hook
  - Delegates to HooksManager
  - Logs operation

- `register_hook_callback(hook_name, callback, priority=10, context=None)`
  - Registers callback
  - Sets priority
  - Handles context
  - Logs details

- `trigger_hook(hook_name, data=None, context=None)`
  - Triggers hook
  - Passes data
  - Filters by context
  - Logs operation

## Configuration

### Manager Initialization
- PluginManager
- ServicesManager
- HooksManager
- ModuleManager
- WebSocketManager

### Template Settings
- Template directories
- Jinja2 loader configuration

## Usage Example
```python
# Initialize app manager
app_manager = AppManager()

# Initialize with Flask app
app_manager.initialize(app)

# Register template directory
app_manager.register_template_dir("/path/to/templates")

# Register hook
app_manager.register_hook("app_startup")

# Register hook callback
def startup_callback(data):
    print("Application starting...")
app_manager.register_hook_callback("app_startup", startup_callback)

# Trigger hook
app_manager.trigger_hook("app_startup", {"status": "initializing"})

# Get plugins path
plugins_path = app_manager.get_plugins_path()
```

## Error Handling
- Validates Flask app
- Handles initialization errors
- Manages template loading
- Implements proper recovery

## Security Considerations
- Validates plugin paths
- Manages template access
- Controls hook execution
- Protects sensitive data

## Best Practices
1. Initialize properly
2. Register templates early
3. Use hooks effectively
4. Handle errors properly
5. Follow security guidelines
6. Test all scenarios
7. Monitor operations
8. Clean up resources
9. Implement proper logging
10. Document hook usage 