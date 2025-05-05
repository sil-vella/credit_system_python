from flask import Flask, jsonify
from flask_cors import CORS
from core.managers.app_manager import AppManager
import sys
import os
from core.metrics import init_metrics

sys.path.append(os.path.abspath(os.path.dirname(__file__)))


# Initialize the AppManager
app_manager = AppManager()

# Initialize the Flask app
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS)
CORS(app)

# Initialize metrics
metrics = init_metrics(app)

# Initialize the AppManager and pass the app for plugin registration
app_manager.initialize(app)

# Additional app-level configurations
app.config["DEBUG"] = True

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Run with WebSocket support
    app_manager.run(app, host='0.0.0.0', port=5000)
