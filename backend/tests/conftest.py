import pytest
from httpx import ASGITransport, AsyncClient

from app.database.session import async_session_factory
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session
