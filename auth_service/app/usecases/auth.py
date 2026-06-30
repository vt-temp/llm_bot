from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError, UserNotFoundError
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.users import UsersRepository
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserPublic


class AuthUseCase:
    """Содержит бизнес-логику регистрации, входа и получения профиля пользователя."""

    def __init__(self, users_repository: UsersRepository) -> None:
        self._users_repository = users_repository

    async def register(self, payload: RegisterRequest) -> UserPublic:
        """Регистрирует нового пользователя и возвращает его публичный профиль."""
        existing_user = await self._users_repository.get_by_email(payload.email)
        if existing_user is not None:
            raise UserAlreadyExistsError()

        user = await self._users_repository.create(
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        return UserPublic.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        """Проверяет учетные данные пользователя и выдает JWT."""
        user = await self._users_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        token = create_access_token(subject=str(user.id), role=user.role)
        return TokenResponse(access_token=token)

    async def me(self, user_id: int) -> UserPublic:
        """Возвращает публичные данные пользователя по его идентификатору."""
        user = await self._users_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return UserPublic.model_validate(user)