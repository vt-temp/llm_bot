from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.db.base import Base
from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_register_login_and_me_flow(client: AsyncClient) -> None:
    register_response = await client.post(
        "/auth/register",
        json={"email": "surname@email.com", "password": "StrongPass123"},
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/auth/login",
        data={"username": "surname@email.com", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "surname@email.com"


@pytest.mark.asyncio
async def test_duplicate_registration_returns_409(client: AsyncClient) -> None:
    payload = {"email": "surname@email.com", "password": "StrongPass123"}
    first_response = await client.post("/auth/register", json=payload)
    second_response = await client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/auth/register",
        json={"email": "surname@email.com", "password": "StrongPass123"},
    )

    login_response = await client.post(
        "/auth/login",
        data={"username": "surname@email.com", "password": "WrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert login_response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401