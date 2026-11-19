import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _database_uri() -> str:
    """Возвращает URI БД: PostgreSQL из DATABASE_URL или локальный SQLite."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    if url:
        return url
    return f"sqlite:///{(BASE_DIR / 'instance' / 'glamping.db').as_posix()}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    UPLOAD_FOLDER = str(BASE_DIR / "app" / "static" / "uploads")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
    ITEMS_PER_PAGE = 9

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
