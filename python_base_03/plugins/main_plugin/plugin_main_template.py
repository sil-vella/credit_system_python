from tools.logger.custom_logging import custom_log
from flask import request, jsonify

class TemplatePlugin:
    def initialize(self, app_manager):
        """
        Initialize the TemplatePlugin with AppManager.
        :param app_manager: AppManager - The main application manager.
        """
        custom_log("Initializing TemplatePlugin...")

        try:
            # First, ensure ConnectionAPI is available
            connection_api = app_manager.module_manager.get_module("connection_api")
            if not connection_api:
                raise RuntimeError("ConnectionAPI is not registered in ModuleManager.")

            # Register function helper module
            app_manager.module_manager.register_module(
                "function_helper_module", 
                FunctionHelperModule, 
                app_manager=app_manager
            )

            # Register API routes
            self._register_routes(app_manager)

            custom_log("TemplatePlugin initialized successfully")

        except Exception as e:
            custom_log(f"Error initializing TemplatePlugin: {e}")
            raise

    def _register_routes(self, app_manager):
        """Register API routes for the plugin."""
        @app_manager.flask_app.route('/api/template', methods=['POST'])
        def temaplate_method():
            try:
                # Get user data from JWT token
                return()
            
            except Exception as e:
                custom_log(f"Error: {e}")
                return jsonify({'error': str(e)}), 500