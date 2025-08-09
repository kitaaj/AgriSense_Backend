
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "a-very-secret-key"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "src", "database", "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "super-secret-jwt-key"
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 24 * 60 * 60)) # 24 hours

    # Logging Configuration
    LOG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "agrisense.log")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "INFO"

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}
