import os
import sys
import logging
from logging.handlers import RotatingFileHandler

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.farm import farm_bp
from src.routes.soil_analysis import soil_bp
from src.routes.utils import utils_bp
from src.middleware.error_handlers import register_error_handlers
from src.middleware.request_logging import setup_request_logging

# Import the new Config class
from config import config_by_name

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Load configuration from config.py
config_name = os.environ.get("FLASK_CONFIG", "development")
app.config.from_object(config_by_name[config_name])



# Configuration from app.config (These lines are redundant if loaded from config.py, but harmless)
app.config["SECRET_KEY"] = app.config.get("SECRET_KEY")
app.config["JWT_SECRET_KEY"] = app.config.get("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get("SQLALCHEMY_DATABASE_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = app.config.get("SQLALCHEMY_TRACK_MODIFICATIONS")

log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs') # Point to agrisense-backend/logs
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Define the log file path directly
LOG_FILE_PATH = os.path.join(log_dir, 'agrisense.log')

# Set up file handler for logging
file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
# Set level to DEBUG to capture all messages
file_handler.setLevel(logging.DEBUG)

# Add the file handler to the Flask app's logger
app.logger.addHandler(file_handler)
# Set the app's logger level to DEBUG as well
app.logger.setLevel(logging.DEBUG)


# Enable CORS for all routes
CORS(app, origins="*")

# Initialize JWT
jwt = JWTManager(app)

# Add JWT configuration
app.config["JWT_TOKEN_LOCATION"] = ["headers"] # <-- ADD THIS LINE
app.config["JWT_HEADER_NAME"] = "Authorization" # Default, but good to be explicit
app.config["JWT_HEADER_TYPE"] = "Bearer" # Default, but good to be explicit


# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(farm_bp, url_prefix="/api")
app.register_blueprint(soil_bp, url_prefix="/api")
app.register_blueprint(utils_bp, url_prefix="/api")
app.register_blueprint(user_bp, url_prefix="/api")


# Setup middleware
register_error_handlers(app)
setup_request_logging(app)


# Database configuration
db.init_app(app)


# Import all models to ensure they are registered
from src.models.farm import Farm
from src.models.soil_analysis import SoilAnalysis, Recommendation

with app.app_context():
    db.create_all()


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, "index.html")
        else:
            return "AgriSense API is running", 200

def health_check():
    """Health check endpoint"""
    app.logger.info("Health check endpoint accessed")
    return {"status": "healthy", "service": "AgriSense API"}, 200

@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"404 Not Found: {request.url}")
    return jsonify({"error": "Not Found", "message": "The requested URL was not found on the server."}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.exception(f"500 Internal Server Error: {request.url}")
    return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred on the server."}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
