import os
import json
from tools.logger.custom_logging import custom_log, log_function_call
from utils.config.config import Config
from flask import request


class TemplateModule:
    def __init__(self, app_manager=None):
        """Initialize the TemplateModule"""
        self.registered_routes = []
        self.app = None  # Reference to Flask app
        self.app_manager = app_manager  # Reference to AppManager if provided
