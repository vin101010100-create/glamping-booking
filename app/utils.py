import os
import re
import uuid
from datetime import datetime
from urllib.parse import urljoin, urlparse

from flask import current_app, request

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
DATE_FORMAT = "%Y-%m-%d"


def parse_date(value: str | None):
    """Разбирает дату формата YYYY-MM-DD, возвращает None при ошибке."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date()
    except (ValueError, AttributeError):
        return None


def is_safe_url(target: str | None) -> bool:
    """Защита от open redirect: разрешаем только внутренние ссылки."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def save_uploaded_image(file_storage) -> str | None:
    """Сохраняет изображение с уникальным именем. Возвращает путь для БД."""
    if file_storage is None or not file_storage.filename:
        return None

    extension = file_storage.filename.rsplit(".", 1)[-1].lower()
    if extension not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return None

    filename = f"{uuid.uuid4().hex}.{extension}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    file_storage.save(os.path.join(upload_folder, filename))
    return f"uploads/{filename}"


def remove_uploaded_image(path: str | None) -> None:
    """Удаляет ранее загруженный файл (только из папки uploads)."""
    if not path or not path.startswith("uploads/"):
        return
    filename = os.path.basename(path)
    full_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if os.path.isfile(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass
