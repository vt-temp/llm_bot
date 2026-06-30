from datetime import UTC, datetime, timedelta

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Хеширует пароль пользователя для безопасного хранения в БД."""
    password_bytes = password.encode("utf-8")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет соответствие введенного пароля сохраненному хешу."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Создает JWT с идентификатором пользователя, ролью и временем жизни."""
    now = datetime.now(UTC)
    expire_at = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str) -> dict:
    """Декодирует и валидирует JWT по подписи и алгоритму."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])


__all__ = [
    "ExpiredSignatureError",
    "JWTError",
    "create_access_token",
    "decode_token",
    "hash_password",
    "verify_password",
]