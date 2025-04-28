import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_permissions_and_roles_crud(client: AsyncClient):
    # Auth
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "Pass1234!"
    r = await client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201
    uid = r.json().get("id")
    login = await client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # 1) Get default user permissions
    perms_resp = await client.get(f"/permissions/users/{uid}", headers=headers)
    assert perms_resp.status_code == 200
    perms = perms_resp.json()
    assert perms.get("user_id") == uid
    assert isinstance(perms.get("can_view_users"), bool)

    # 2) Roles CRUD
    # Create role
    role_name = f"Role_{uuid.uuid4().hex[:6]}"
    create_role = await client.post(
    "/permissions/roles",
    headers=headers,
    json={"name": role_name})  # <-- ici, on envoie le JSON attendu
    print("Role created:", create_role.json())
    assert create_role.status_code == 200
    role = create_role.json()
    rid = role.get("id")
    assert role.get("name") == role_name

    # List roles and confirm creation
    new_list = await client.get("/permissions/roles", headers=headers)
    print("Role list:", new_list.json())
    assert any(r.get("id") == rid for r in new_list.json())

    # Get role by ID
    get_r = await client.get(f"/permissions/roles/{rid}", headers=headers)
    assert get_r.status_code == 200
    assert get_r.json().get("id") == rid

    # Update role
    new_name = f"UpdatedRole_{uuid.uuid4().hex[:6]}"
    upd_r = await client.put(
        f"/permissions/roles/{rid}",
        json={"name": new_name},  # Send name in JSON body
        headers=headers
    )
    print("Update Role response:", upd_r.json())

    assert upd_r.status_code == 200
    assert upd_r.json().get("name") == new_name

    # Delete role
    del_r = await client.delete(f"/permissions/roles/{rid}", headers=headers)
    assert del_r.status_code == 200

    # Ensure removed
    final = await client.get("/permissions/roles", headers=headers)
    assert not any(r.get("id") == rid for r in final.json())

    # 3) Permissions listing
    list_perm = await client.get("/permissions/permissions", headers=headers)
    assert list_perm.status_code == 200
    perms_list = list_perm.json()
    assert isinstance(perms_list, list)
    if perms_list:
        pid = perms_list[0].get("id")
        gp = await client.get(f"/permissions/permissions/{pid}", headers=headers)
        assert gp.status_code == 200
        assert gp.json().get("id") == pid

    # 4) Update user permissions without rights -> should fail 400
    upd_user_perm = await client.put(f"/permissions/update_permissions/{uid}", json={"can_view_users": True}, headers=headers)
    assert upd_user_perm.status_code == 400
    assert "Vous n'avez pas" in upd_user_perm.json().get("detail", "")


@pytest.mark.asyncio
async def test_invalid_role_creation(client: AsyncClient):
    # Create a user and try to create a role without providing a name
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "Pass1234!"
    r = await client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201
    login = await client.post("/auth/login", data={"username": email, "password": password})
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Missing query parameter 'name'
    create_role = await client.post("/permissions/roles", headers=headers)
    # Expecting an error (status != 200)
    assert create_role.status_code != 200


@pytest.mark.asyncio
async def test_get_non_existing_role(client: AsyncClient):
    # Create a user and try to retrieve a role that does not exist.
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "Pass1234!"
    r = await client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201
    login = await client.post("/auth/login", data={"username": email, "password": password})
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    fake_role_id = 999999  # Assuming this ID does not exist
    get_role = await client.get(f"/permissions/roles/{fake_role_id}", headers=headers)
    assert get_role.status_code == 404


@pytest.mark.asyncio
async def test_list_roles_empty(client: AsyncClient):
    # Create a fresh user and verify listing roles (could be empty or have default roles)
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "Pass1234!"
    r = await client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201
    login = await client.post("/auth/login", data={"username": email, "password": password})
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    list_roles = await client.get("/permissions/roles", headers=headers)
    roles = list_roles.json()
    assert isinstance(roles, list)


@pytest.mark.asyncio
async def test_update_user_permissions_with_admin_rights(client: AsyncClient):
    # Create an admin user (assuming signup grants proper rights for self-permission management)
    email_admin = f"admin_{uuid.uuid4().hex}@example.com"
    password = "Pass1234!"
    r_admin = await client.post("/auth/signup", json={"email": email_admin, "password": password})
    assert r_admin.status_code == 201
    login_admin = await client.post("/auth/login", data={"username": email_admin, "password": password})
    token_admin = login_admin.json().get("access_token")
    headers_admin = {"Authorization": f"Bearer {token_admin}"}
    admin_id = r_admin.json().get("id")

    # Update own permissions assuming admin privileges allow it.
    upd_resp = await client.put(f"/permissions/update_permissions/{admin_id}", json={"can_view_users": False}, headers=headers_admin)
    assert upd_resp.status_code == 400
    # Optionnel : vérifier le message d’erreur
    assert "Vous n'avez pas" in upd_resp.json().get("detail", "")

# "Configurer l’infrastructure de tests" - This section can be used to set up shared fixtures,
# initialize test databases, or perform common configuration.
# For instance, if you use a fixture to create an AsyncClient:
#
# @pytest.fixture(scope="session")
# async def client() -> AsyncClient:
#     async with AsyncClient(base_url="http://testserver") as ac:
#         yield ac
