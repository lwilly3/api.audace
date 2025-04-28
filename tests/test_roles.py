import pytest
import uuid
from httpx import AsyncClient

# Refactored to async tests using AsyncClient
@pytest.mark.asyncio
async def test_list_and_get_roles(client: AsyncClient):
    # 1. Signup a user and login
    email = f"role_user_{uuid.uuid4().hex}@example.com"
    password = "TestPass123!"
    signup = await client.post("/auth/signup", json={"email": email, "password": password})
    assert signup.status_code == 201
    login = await client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a new role
    role_name = f"ListRole_{uuid.uuid4().hex[:6]}"
    resp_create = await client.post(
        "/roles/", json={"name": role_name}, headers=headers
    )
    assert resp_create.status_code == 201
    created = resp_create.json()
    role_id = created.get("id")
    assert created.get("name") == role_name

    # 3. List roles and verify the created one is present
    list_resp = await client.get("/roles/all", headers=headers)
    assert list_resp.status_code == 200
    roles = list_resp.json()
    assert any(r.get("id") == role_id for r in roles)

    # 4. Retrieve the specific role by ID
    get_resp = await client.get(f"/roles/id/{role_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json().get("id") == role_id

@pytest.mark.asyncio
async def test_get_role_not_found(client: AsyncClient):
    # Use a non-existent integer ID to test not found
    non_existent = 999999  # ID format must be integer
    # Signup & login for token
    email = f"role_test_{uuid.uuid4().hex}@example.com"
    password = "TestPass123!"
    await client.post("/auth/signup", json={"email": email, "password": password})
    login = await client.post("/auth/login", data={"username": email, "password": password})
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get(f"/roles/id/{non_existent}", headers=headers)
    assert resp.status_code == 404  # Not found for non-existent integer ID

@pytest.mark.asyncio
async def test_create_role_public_by_regular_user(client: AsyncClient):
    # Public API allows role creation; ensure user can create a role
    email = f"role_user2_{uuid.uuid4().hex}@example.com"
    password = "TestPass123!"
    await client.post("/auth/signup", json={"email": email, "password": password})
    login = await client.post("/auth/login", data={"username": email, "password": password})
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    data = {"name": f"PublicCreatedRole_{uuid.uuid4().hex}", "description": "Created by regular user"}
    create_resp = await client.post("/roles/", json=data, headers=headers)
    print("Create Role response:", create_resp.json())
    assert create_resp.status_code == 201  # Public creation succeeded
    resp_data = create_resp.json()
    assert resp_data.get("name") == data["name"]
    # The response_model RoleRead includes id, name and users; description is not returned
    assert "id" in resp_data
    assert "users" in resp_data and isinstance(resp_data["users"], list)

# TODO: Add tests for creation/update/delete success for admin users once admin fixture is available