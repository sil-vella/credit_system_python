from core.managers.plugin_manager import PluginManager
from core.managers.service_manager import ServicesManager
from core.managers.hooks_manager import HooksManager
from core.managers.module_manager import ModuleManager
from core.managers.websocket_manager import WebSocketManager
from core.managers.rate_limiter_manager import RateLimiterManager
from jinja2 import ChoiceLoader, FileSystemLoader
from tools.logger.custom_logging import custom_log, function_log, game_play_log, log_function_call
import os
from flask import request
import time
from utils.config.config import Config
from redis.exceptions import RedisError


class AppManager:
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.services_manager = ServicesManager()
        self.hooks_manager = HooksManager()
        self.module_manager = ModuleManager()
        self.websocket_manager = WebSocketManager()
        self.rate_limiter_manager = RateLimiterManager()
        self.template_dirs = []  # List to track template directories
        self.flask_app = None  # Flask app reference

        custom_log("AppManager instance created.")

    @log_function_call
    def initialize(self, app):
        """
        Initialize all components and plugins.
        """
        # Set the Flask app
        if not hasattr(app, "add_url_rule"):
            raise RuntimeError("AppManager requires a valid Flask app instance.")

        self.flask_app = app
        custom_log(f"AppManager initialized with Flask app: {self.flask_app}")

        # Initialize services
        self.services_manager.initialize_services()

        # Initialize WebSocket support
        self.websocket_manager.initialize(app)

        # Register and initialize plugins
        custom_log("Initializing plugins...")
        self.plugin_manager.register_plugins(self)

        # Update the Jinja loader with template directories
        self._update_jinja_loader()

        # Initialize rate limiting middleware
        self._setup_rate_limiting()

    def run(self, app, **kwargs):
        """Run the Flask application with WebSocket support."""
        self.websocket_manager.run(app, **kwargs)

    @log_function_call
    def get_plugins_path(self, return_url=False):
        """
        Retrieve the absolute path or the URL path for the plugins directory.

        :param return_url: If True, return the URL path for plugins; otherwise, return the absolute path.
        :return: String representing either the full path or the URL path.
        """
        try:
            # Get the absolute path of this file's directory (/app/core/)
            core_path = os.path.abspath(os.path.dirname(__file__))  
            
            # Move TWO levels up to reach /app/
            project_root = os.path.dirname(os.path.dirname(core_path))  

            # Now plugins should be correctly at /app/plugins
            plugins_dir = os.path.join(project_root, "plugins")  

            if return_url:
                if not self.flask_app:
                    raise RuntimeError("Flask app is not initialized in AppManager.")
                
                base_url = request.host_url.rstrip('/')
                return f"{base_url}/plugins"

            # Ensure the directory exists before returning
            if not os.path.exists(plugins_dir):
                custom_log(f"Warning: Plugins directory does not exist at {plugins_dir}")
                return None

            return plugins_dir
        except Exception as e:
            custom_log(f"Error retrieving plugins path: {e}")
            return None

    @log_function_call
    def register_template_dir(self, template_dir):
        """
        Register a template directory with the Flask app.
        :param template_dir: Path to the template directory.
        """
        if template_dir not in self.template_dirs:
            self.template_dirs.append(template_dir)
            custom_log(f"Template directory '{template_dir}' registered.")

    @log_function_call
    def _update_jinja_loader(self):
        """
        Update the Flask app's Jinja2 loader to include all registered template directories.
        """
        if not self.flask_app:
            raise RuntimeError("Flask app is not initialized in AppManager.")

        self.flask_app.jinja_loader = ChoiceLoader([
            FileSystemLoader(template_dir) for template_dir in self.template_dirs
        ])
        custom_log("Flask Jinja loader updated with registered template directories.")

    @log_function_call
    def _setup_rate_limiting(self):
        """Set up rate limiting middleware for the Flask app."""
        if not self.flask_app:
            return

        @self.flask_app.before_request
        def check_rate_limit():
            """Middleware to check rate limits before each request."""
            # Skip rate limiting for OPTIONS requests (CORS preflight)
            if request.method == 'OPTIONS':
                return None

            try:
                # Check IP-based rate limit
                result = self.rate_limiter_manager.check_rate_limit('ip')
                
                if not result['allowed']:
                    # Log rate limit hit
                    custom_log(f"Rate limit exceeded for IP: {request.remote_addr}", level="WARNING")
                    
                    # Rate limit exceeded
                    from flask import make_response, jsonify
                    response = make_response(
                        jsonify({
                            'error': 'Rate limit exceeded',
                            'message': 'Too many requests',
                            'retry_after': result['reset_time'] - int(time.time())
                        }),
                        429  # Too Many Requests
                    )
                    
                    # Add rate limit headers if enabled
                    if Config.RATE_LIMIT_HEADERS_ENABLED:
                        response.headers[Config.RATE_LIMIT_HEADER_LIMIT] = str(self.rate_limiter_manager.config['ip']['requests'])
                        response.headers[Config.RATE_LIMIT_HEADER_REMAINING] = str(result['remaining'])
                        response.headers[Config.RATE_LIMIT_HEADER_RESET] = str(result['reset_time'])
                    
                    return response

                # Log rate limit status for monitoring
                if result['remaining'] < 10:  # Log when getting close to limit
                    custom_log(f"Rate limit warning for IP: {request.remote_addr}. Remaining: {result['remaining']}", level="WARNING")

            except RedisError as e:
                # Log Redis errors but allow the request to proceed
                custom_log(f"Redis error in rate limiting: {str(e)}", level="ERROR")
                return None
            except Exception as e:
                # Log other errors but allow the request to proceed
                custom_log(f"Error in rate limiting: {str(e)}", level="ERROR")
                return None

            # Add rate limit headers to successful responses
            @self.flask_app.after_request
            def add_rate_limit_headers(response):
                try:
                    if Config.RATE_LIMIT_HEADERS_ENABLED:
                        response.headers[Config.RATE_LIMIT_HEADER_LIMIT] = str(self.rate_limiter_manager.config['ip']['requests'])
                        response.headers[Config.RATE_LIMIT_HEADER_REMAINING] = str(result['remaining'])
                        response.headers[Config.RATE_LIMIT_HEADER_RESET] = str(result['reset_time'])
                except Exception as e:
                    custom_log(f"Error adding rate limit headers: {str(e)}", level="ERROR")
                return response

    @log_function_call
    def register_hook(self, hook_name):
        """
        Register a new hook by delegating to the HooksManager.
        :param hook_name: str - The name of the hook.
        """
        self.hooks_manager.register_hook(hook_name)
        custom_log(f"Hook '{hook_name}' registered via AppManager.")

    @log_function_call
    def register_hook_callback(self, hook_name, callback, priority=10, context=None):
        """
        Register a callback for a specific hook by delegating to the HooksManager.
        :param hook_name: str - The name of the hook.
        :param callback: callable - The callback function.
        :param priority: int - Priority of the callback (lower number = higher priority).
        :param context: str - Optional context for the callback.
        """
        self.hooks_manager.register_hook_callback(hook_name, callback, priority, context)
        callback_name = callback.__name__ if hasattr(callback, "__name__") else str(callback)
        custom_log(f"Callback '{callback_name}' registered for hook '{hook_name}' (priority: {priority}, context: {context}).")

    @log_function_call
    def trigger_hook(self, hook_name, data=None, context=None):
        """
        Trigger a specific hook by delegating to the HooksManager.
        :param hook_name: str - The name of the hook to trigger.
        :param data: Any - Data to pass to the callback.
        :param context: str - Optional context to filter callbacks.
        """
        custom_log(f"Triggering hook '{hook_name}' with data: {data} and context: {context}.")
        self.hooks_manager.trigger_hook(hook_name, data, context)
