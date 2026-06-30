from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.jwt import TokenExpiredError, TokenValidationError, decode_and_validate


def make_token(payload: dict) -> str:
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def test_decode_and_validate_accepts_valid_token() -> None:
    now = datetime.now(UTC)
    token = make_token(
        {
            "sub": "1",
            "role": "user",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        }
    )

    payload = decode_and_validate(token)

    assert payload["sub"] == "1"


def test_decode_and_validate_rejects_invalid_token() -> None:
    with pytest.raises(TokenValidationError):
        decode_and_validate("invalid-token")


def test_decode_and_validate_rejects_expired_token() -> None:
    now = datetime.now(UTC)
    token = make_token(
        {
            "sub": "1",
            "role": "user",
            "iat": int(now.timestamp()),
            "exp": int((now - timedelta(minutes=5)).timestamp()),
        }
    )

    with pytest.raises(TokenExpiredError):
        decode_and_validate(token)