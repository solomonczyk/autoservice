import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.db.session import Base, get_db
from app.core.config import settings

# MOCK SETTINGS FOR TEST
settings.TELEGRAM_BOT_TOKEN = "123456789:AABBCCDDEEFFaabbccddeeff" # Valid format mock

from app.db.session import Base, get_db
from app.main import app
from app.models.models import User, Shop
from app.core.security import get_password_hash

# Use an in-memory SQLite database for testing, or a separate test DB
# For this example, we'll use the existing Postgres but with a different DB name if possible, 
# or just mock the session. 
# BETTER: Use a separate test database. 
# For MVP speed, let's use the same DB but different tables or transaction rollback?
# Transaction rollback is safest.

# OVERRIDE DEPENDENCY
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Pass for now, we will rely on the app's dependency injection override if needed
    # But for integration tests, we want to actually hit the DB.
    pass

# Helper to create a user and get token
@pytest.fixture
async def normal_user_token(client: AsyncClient) -> str:
    # 1. Create User (via direct DB call or API if open)
    # Since we don't have a register endpoint, we must seed it directly or use the one we created.
    # Let's assume 'admin' exists from our seed script.
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": "admin", "password": "admin"},
        headers={"content-type": "application/x-www-form-urlencoded"}
    )
    return response.json()["access_token"]
