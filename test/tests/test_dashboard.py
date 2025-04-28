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

    # 2. Request dashboard stats
    resp = await client.get("/dashboard/stats", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    # Verify expected keys and types
    assert "user_count" in data and isinstance(data["user_count"], int)
    assert "emission_count" in data and isinstance(data["emission_count"], int)
    assert "show_count" in data and isinstance(data["show_count"], int)

@pytest.mark.asyncio
async def test_get_dashboard_stats_unauthorized(client: AsyncClient):
    # Without token, should be unauthorized
    resp = await client.get("/dashboard/stats")
    assert resp.status_code == 401
