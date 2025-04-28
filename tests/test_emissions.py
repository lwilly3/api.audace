import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_emission_crud_and_soft_delete(client: AsyncClient):
    # Auth: créer un utilisateur et se connecter
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "Pass1234!"
    # Signup
    r = await client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201
    user_id = r.json().get("id")
    # Login
    login = await client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Create emission
    data = {
        "title": f"Emission {uuid.uuid4().hex[:6]}",
        "synopsis": "Synopsis test",
        "type": "TypeX",
        "duration": 45,
        "frequency": "Hebdo",
        "description": "Test description"
    }
    create_resp = await client.post("/emissions/", json=data, headers=headers)
    assert create_resp.status_code == 200
    emitted = create_resp.json()
    eid = emitted.get("id")
    assert emitted.get("title") == data["title"]

    # List emissions
    list_resp = await client.get("/emissions/?skip=0&limit=10", headers=headers)
    assert list_resp.status_code == 200
    arr = list_resp.json()
    assert any(item.get("id") == eid for item in arr)

    # Get by ID
    get_resp = await client.get(f"/emissions/{eid}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json().get("id") == eid

    # Update emission
    new_title = "Updated Title"
    upd_resp = await client.put(f"/emissions/upd/{eid}", json={"title": new_title}, headers=headers)
    assert upd_resp.status_code == 200
    assert upd_resp.json().get("title") == new_title

    # Soft delete
    soft_resp = await client.delete(f"/emissions/softDel/{eid}", headers=headers)
    assert soft_resp.status_code == 200
    assert soft_resp.json() is True

    # Hard delete
    del_resp = await client.delete(f"/emissions/del/{eid}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json() is True

    # Verify not found
    nf = await client.get(f"/emissions/{eid}", headers=headers)
    assert nf.status_code == 404
