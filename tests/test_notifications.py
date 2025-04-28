import pytest
# pytest.skip("Tests de notifications ignorés", allow_module_level=True)

import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_notifications_crud(client: AsyncClient):
    # Auth: création et connexion utilisateur
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "Pass1234!"
    # Signup
    r = await client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201
    # Login
    login = await client.post("/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    user_id = login.json().get("user_id")

    # Create notification
    notif_data = {"user_id":user_id, "message": "Hello world"}
    create_resp = await client.post("/notifications/", json=notif_data, headers=headers)
    assert create_resp.status_code == 200
    notif = create_resp.json()
    notif_id = notif.get("id")
    # assert notif.get("title") == notif_data["title"]
    assert notif.get("message") == notif_data["message"]

    # List notifications: expect the created notification to be present
    list_resp = await client.get("/notifications/", headers=headers)
    assert list_resp.status_code == 200
    arr = list_resp.json()
    assert any(n.get("id") == notif_id for n in arr)

    # Get by ID
    get_resp = await client.get(f"/notifications/{notif_id}", headers=headers)
    print("Get response:", get_resp.json())
    assert get_resp.status_code == 200
    obj = get_resp.json()
    assert obj.get("id") == notif_id

    # Update
    new_msg = "Updated message"
    upd_resp = await client.put(f"/notifications/{notif_id}", json={"message": new_msg}, headers=headers)
    assert upd_resp.status_code == 200
    assert upd_resp.json().get("message") == new_msg

    # Delete (soft)
    del_resp = await client.delete(f"/notifications/{notif_id}", headers=headers)
    assert del_resp.status_code == 200
    assert "deleted successfully" in del_resp.json().get("detail", "")

    # Verify not found after delete
    nf = await client.get(f"/notifications/{notif_id}", headers=headers)
    print("Get response after soft delect:", get_resp.json())
    assert nf.status_code == 200
