import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_login_access_token(client: AsyncClient):
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token", 
        data=login_data,
        headers={"content-type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["access_token"]

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    login_data = {
        "username": "admin",
        "password": "wrongpassword"
    }
    response = await client.post(
        f"{settings.API_V1_STR}/login/access-token", 
        data=login_data,
        headers={"content-type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 400
