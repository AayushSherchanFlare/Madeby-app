import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "madeby")

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    MAIL_SUPPRESS_SEND = False

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_ROOT = BASE_DIR / "app" / "static" / "uploads"
    PROFILE_UPLOAD_FOLDER = UPLOAD_ROOT / "profiles"
    COVER_UPLOAD_FOLDER = UPLOAD_ROOT / "covers"
    PROJECT_UPLOAD_FOLDER = UPLOAD_ROOT / "projects"
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Flask-WTF passes this value to itsdangerous, which expects seconds.
    WTF_CSRF_TIME_LIMIT = 60 * 60
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SECRET_KEY = "test-secret-key"
    MAIL_SUPPRESS_SEND = True
