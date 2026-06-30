from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


class UserAlreadyExistsError(BaseHTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "Пользователь с таким email уже существует")


class InvalidCredentialsError(BaseHTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")


class InvalidTokenError(BaseHTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Некорректный токен")


class TokenExpiredError(BaseHTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "Срок действия токена истек")


class UserNotFoundError(BaseHTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "Пользователь не найден")


class PermissionDeniedError(BaseHTTPException):
    def __init__(self) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "Недостаточно прав")