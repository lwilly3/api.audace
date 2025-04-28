import pytest
from httpx import AsyncClient
from random import randint

@pytest.mark.asyncio
async def test_guest_crud_search_and_details(client: AsyncClient):
    # Création d'un utilisateur pour l'authentification
    email = f"user{randint(1000,9999)}@example.com"
    password = "Pass1234!"
    # Signup
    resp = await client.post("/auth/signup", json={"email": email, "password": password})
    assert resp.status_code == 201
    # Login
    login = await client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Create guest
    guest_data = {
        "name": f"Guest{randint(100,999)}",
        "contact_info": "contact info",
        "biography": "bio",
        "role": "role_x",
        "phone": "123456",
        "email": f"guest{randint(100,999)}@example.com",
        "avart": "http://avatar.url"
    }
    create_resp = await client.post("/guests/", json=guest_data, headers=headers)
    assert create_resp.status_code == 200
    guest = create_resp.json()
    guest_id = guest.get("id")

    # Get list
    list_resp = await client.get("/guests/?skip=0&limit=10", headers=headers)
    assert list_resp.status_code == 200
    data_list = list_resp.json()
    assert any(g["id"] == guest_id for g in data_list)

    # Get by ID
    get_resp = await client.get(f"/guests/{guest_id}", headers=headers)
    assert get_resp.status_code == 200
    result = get_resp.json()
    assert result.get("email") == guest_data["email"]

    # Update
    new_role = "updated_role"
    update_resp = await client.put(f"/guests/{guest_id}", json={"role": new_role}, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json().get("role") == new_role

    # Search
    search_resp = await client.get(f"/guests/search?query={guest_data['name']}")
    assert search_resp.status_code == 200
    search_json = search_resp.json()
    assert search_json.get("status_code") == 200
    assert any(item["id"] == guest_id for item in search_json.get("data", []))

    # Details
    details_resp = await client.get(f"/guests/details/{guest_id}", headers=headers)
    assert details_resp.status_code == 200
    details = details_resp.json()
    assert details.get("id") == guest_id
    assert isinstance(details.get("appearances"), list)

    # Delete
    delete_resp = await client.delete(f"/guests/{guest_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json().get("message")

    # Verify deletion
    not_found = await client.get(f"/guests/{guest_id}", headers=headers)
    assert not_found.status_code == 404
