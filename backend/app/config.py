"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import secrets
import string
import json
import os


def load_ports_config() -> dict:
    """Load ports configuration from ports.json in project root."""
    # Project root is two levels up from app/ (app/ -> backend/ -> project root)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ports_file = os.path.join(backend_dir, '..', 'ports.json')
    try:
        with open(ports_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def generate_secure_secret(length: int = 64) -> str:
    """Generate a cryptographically secure random string."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Training Platform"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_PORT: int = 8003  # Default port, can be overridden by ports.json

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "training_platform"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # JWT - Generate secure secret if not provided
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER: int = 60 * 24 * 7  # 7 days when "remember me" is checked
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OSS (Object Storage)
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY: str = ""
    OSS_SECRET_KEY: str = ""
    OSS_BUCKET: str = ""
    OSS_REGION: str = "cn-hangzhou"

    # SMTP Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # Security
    BCRYPT_ROUNDS: int = 12
    LOGIN_MAX_FAILED_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_DURATION_MINUTES: int = 15

    # Video Encryption
    VIDEO_ENCRYPTION_ALGORITHM: str = "AES-128"
    VIDEO_HLS_SEGMENT_DURATION: int = 10
    VIDEO_PLAY_TOKEN_VALIDITY_SECONDS: int = 30

    # File Upload
    MAX_VIDEO_SIZE: int = 2 * 1024 * 1024 * 1024  # 2GB
    MAX_DOCUMENT_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_VIDEO_EXTENSIONS: list = ["mp4", "avi", "mov"]
    ALLOWED_DOCUMENT_EXTENSIONS: list = ["pdf", "doc", "docx"]

    # CORS - Comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:5177,http://localhost:5178,http://localhost:5179,http://localhost:5180,http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load port configuration from ports.json
        ports_config = load_ports_config()
        if ports_config.get('backend'):
            self.BACKEND_PORT = ports_config['backend']
        # Generate secure JWT secret if not set
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = generate_secure_secret(64)
            print(f"WARNING: Generated random JWT_SECRET_KEY. Set JWT_SECRET_KEY in .env for production!")
        # Parse CORS_ORIGINS from comma-separated string to list
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()