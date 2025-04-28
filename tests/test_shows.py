import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_show_crud_and_status(client: AsyncClient):
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

    # Create show
    show_data = {
        "title": "TestShow",
        "type": "TypeX",
        "broadcast_date": None,
        "duration": 60,
        "frequency": "Hebdo",
        "description": "Desc",
        "status": "active",
        "emission_id": None
    }
    create_resp = await client.post("/shows/", json=show_data, headers=headers)
    assert create_resp.status_code == 201
    show = create_resp.json()
    sid = show.get("id")
    assert show.get("title") == show_data["title"]

    # List shows
    list_resp = await client.get("/shows/?skip=0&limit=100", headers=headers)
    assert list_resp.status_code == 200
    arr = list_resp.json()
    print("List of shows:", arr)
    assert any(item.get("id") == sid for item in arr)

    # Get by ID
    get_resp = await client.get(f"/shows/{sid}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json().get("id") == sid

    # Update
    new_title = "UpdatedShow"
    upd_resp = await client.put(f"/shows/upd/{sid}", json={"title": new_title}, headers=headers)
    assert upd_resp.status_code == 200
    assert upd_resp.json().get("title") == new_title

    # Patch status
    patch_resp = await client.patch(f"/shows/status/{sid}", json={"status": "ended"}, headers=headers)
    assert patch_resp.status_code == 200
    # GET and confirm status changed
    details = (await client.get(f"/shows/{sid}", headers=headers)).json()
    assert details.get("status") == "ended"

    # Delete show
    del_resp = await client.delete(f"/shows/del/{sid}", headers=headers)
    assert del_resp.status_code == 200
    # After delete, GET should 404
    nf = await client.get(f"/shows/{sid}", headers=headers)
    assert nf.status_code == 404
