import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_segment_crud_and_soft_delete(client: AsyncClient):
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

    # Créer une émission pour avoir un show_id
    show_data = {"title": "SegTestShow", "type": "TypeA", "duration": 30, "status": "active"}
    show_resp = await client.post("/shows/", json=show_data, headers=headers)
    assert show_resp.status_code == 201
    show_id = show_resp.json().get("id")

    # Create segment
    seg_data = {
        "title": "Segment1",
        "type": "Interview",
        "duration": 10,
        "description": "desc",
        "technical_notes": "notes",
        "position": 0,
        "show_id": show_id
    }
    create_resp = await client.post("/segments/", json=seg_data, headers=headers)
    # assert create_resp.status_code == 200 # Ancien code
    print("Create Segment response:", create_resp.json())
    assert create_resp.status_code == 201 # Correction: status code 201 pour POST réussi
    segment = create_resp.json()
    sid = segment.get("id")
    assert segment.get("title") == seg_data["title"]

    # List segments
    list_resp = await client.get("/segments/", headers=headers)
    assert list_resp.status_code == 200
    arr = list_resp.json()
    assert any(item.get("id") == sid for item in arr)

    # Get by ID
    get_resp = await client.get(f"/segments/{sid}", headers=headers)
    print("Get Segment response:", get_resp.json())
    assert get_resp.status_code == 200
    assert get_resp.json().get("id") == sid

    # Update
    new_title = "SegmentUpdated"
    upd_resp = await client.put(f"/segments/{sid}", json={"title": new_title}, headers=headers)
    assert upd_resp.status_code == 200
    assert upd_resp.json().get("title") == new_title

    # Update position
    pos_resp = await client.patch(f"/segments/{sid}/position", json={"position": 2}, headers=headers)
    assert pos_resp.status_code == 200
    assert pos_resp.json().get("position") == 2

    # Soft delete
    del_resp = await client.delete(f"/segments/{sid}", headers=headers)
    assert del_resp.status_code == 200
    msg = del_resp.json().get("message") or del_resp.json().get("detail")
    assert "deleted successfully" in msg.lower()

    # Verify not found
    nf = await client.get(f"/segments/{sid}", headers=headers)
    assert nf.status_code == 404
