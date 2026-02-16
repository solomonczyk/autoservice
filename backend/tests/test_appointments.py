import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_create_appointment_unauthorized(client: AsyncClient):
    appt_data = {
        "shop_id": 1, # Should be ignored by backend now
        "service_id": 1,
        "start_time": "2026-02-20T10:00:00",
        "client_name": "Test User",
        "client_phone": "+1234567890"
    }
    response = await client.post(
        f"{settings.API_V1_STR}/appointments/", 
        json=appt_data
    )
    assert response.status_code == 401 # Should prompt for auth

@pytest.mark.asyncio
async def test_create_appointment_authorized(client: AsyncClient):
    # 1. Login to get token
    login_data = {"username": "admin", "password": "admin"}
    login_res = await client.post(
        f"{settings.API_V1_STR}/login/access-token", 
        data=login_data,
        headers={"content-type": "application/x-www-form-urlencoded"}
    )
    token = login_res.json()["access_token"]
    
    # 2. Create Appointment with Token
    appt_data = {
        "service_id": 1,
        "start_time": "2026-02-20T12:00:00",
        "client_name": "Authorized User",
        "client_phone": "+0987654321"
    }
    response = await client.post(
        f"{settings.API_V1_STR}/appointments/", 
        json=appt_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["client_id"] # ID should be assigned
    assert data["shop_id"] == 2 # Admin user belongs to Shop ID 2 (from seed script)
