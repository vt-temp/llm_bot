from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


class TokenValidationError(ValueError):
    pass


class TokenExpiredError(TokenValidationError):
    pass


def decode_and_validate(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("Срок действия токена истек") from exc
    except JWTError as exc:
        raise TokenValidationError("Некорректный токен") from exc

    if not payload.get("sub"):
        raise TokenValidationError("В токене отсутствует sub")

    return payload