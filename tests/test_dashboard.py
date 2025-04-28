import pytest
import uuid
from httpx import AsyncClient

# Test dashboard statistics endpoint
@pytest.mark.asyncio
async def test_get_dashboard_stats_authenticated(client: AsyncClient):
    # 1. Signup and login to obtain a valid token
    email = f"dash_user_{uuid.uuid4().hex}@example.com"
    password = "TestPass123!"
    signup_resp = await client.post(
        "/auth/signup", json={"email": email, "password": password}
    )
    assert signup_resp.status_code == 201

    login_resp = await client.post(
        "/auth/login", data={"username": email, "password": password}
    )
    assert login_resp.status_code == 200
    token = login_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Request dashboard data at the correct path
    resp = await client.get("/dashbord/", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    # Verify expected keys from get_dashboard() return structure
    # (example keys; adapt based on implementation of get_dashboard)
    assert isinstance(data, dict)

@pytest.mark.asyncio
async def test_get_dashboard_stats_unauthorized(client: AsyncClient):
    # Without token, should be unauthorized
    resp = await client.get("/dashbord/")
    assert resp.status_code == 401
