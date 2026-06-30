from collections.abc import AsyncIterator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError, TokenExpiredError, UserNotFoundError
from app.core.security import ExpiredSignatureError, JWTError, decode_token
from app.db.session import AsyncSessionLocal
from app.repositories.users import UsersRepository
from app.usecases.auth import AuthUseCase

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


def get_users_repo(session: AsyncSession = Depends(get_db)) -> UsersRepository:
    return UsersRepository(session)


def get_auth_uc(users_repo: UsersRepository = Depends(get_users_repo)) -> AuthUseCase:
    return AuthUseCase(users_repo)


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = decode_token(token)
    except ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except JWTError as exc:
        raise InvalidTokenError() from exc

    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError()

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError() from exc


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    auth_uc: AuthUseCase = Depends(get_auth_uc),
):
    try:
        return await auth_uc.me(user_id)
    except UserNotFoundError:
        raise