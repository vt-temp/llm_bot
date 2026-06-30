from datetime import timedelta

import pytest
from jose import JWTError

from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_hash_password_returns_hash() -> None:
    password = "StrongPass123"

    password_hash = hash_password(password)

    assert password_hash != password


def test_verify_password_accepts_valid_password() -> None:
    password = "StrongPass123"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_verify_password_rejects_invalid_password() -> None:
    password_hash = hash_password("StrongPass123")

    assert verify_password("WrongPass123", password_hash) is False


def test_create_and_decode_token() -> None:
    token = create_access_token(subject="7", role="user")

    payload = decode_token(token)

    assert payload["sub"] == "7"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_invalid_token_raises_error() -> None:
    with pytest.raises(JWTError):
        decode_token("invalid-token")


def test_expired_token_raises_error() -> None:
    token = create_access_token(subject="7", role="user", expires_delta=timedelta(minutes=-1))

    with pytest.raises(JWTError):
        decode_token(token)