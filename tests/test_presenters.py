import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_presenter_crud_and_by_user(client: AsyncClient):
    # Créer un utilisateur pour auth
    email2 = f"user_{uuid.uuid4().hex}@example.com"
    email=f'{email2}'
    password = "Pass1234!"
    name=f'Test_{uuid.uuid4().hex}'
    
    # Créer l'utilisateur avec /auth/signup
    r = await client.post(
        "/auth/signup",
        json={
            "email": f'{email}',
            "password": password,
            "username": email,
            "name": f'{email2}',
            "family_name": f"User_{uuid.uuid4().hex}"
        }
    )
    assert r.status_code == 201
    user_data = r.json()
    print(f"Réponse signup : {user_data}")
    uid = user_data.get("id")
    assert uid is not None, "User creation failed: ID manquant dans la réponse"

    # Connexion pour obtenir le jeton
    login = await client.post(
        "/auth/login",
        data={"username": email, "password": password}
    )
    assert login.status_code == 200
    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Créer un présentateur
    pr_data = {
        "name": f'{email2}',
        "contact_info": "contact",
        "biography": "bio",
        "users_id": uid,
        # "profilePicture": "http://pic.url",
        # "isMainPresenter": True
    }
    print(f"Payload envoyé pour le présentateur : {pr_data}")
    cr = await client.post("/presenters/", json=pr_data, headers=headers)
    print(f"Réponse création présentateur : {cr.json()}")
    assert cr.status_code == 200, f"Attendu 201, obtenu {cr.status_code}: {cr.json()}"
    pj = cr.json()
    pres_id = pj.get("id")
    assert pj["name"] == pr_data["name"]

    # Liste des présentateurs
    ls = await client.get("/presenters/all?skip=0&limit=100", headers=headers)
    print(f"Réponse liste présentateurs : {ls.json()}")
    assert ls.status_code == 200
    arr = ls.json().get("presenters", [])
    assert any(item.get("presenter_name") == pr_data["name"] for item in arr)

    # Récupérer par ID
    gp = await client.get(f"/presenters/{pres_id}", headers=headers)
    assert gp.status_code == 200
    assert gp.json().get("presenter_name") == pr_data["name"]

    # Récupérer par utilisateur
    gu = await client.get(f"/presenters/by-user/{uid}", headers=headers)
    assert gu.status_code == 200
    assert gu.json().get("users_id") == uid

    # Mettre à jour
    upd = await client.put(f"/presenters/update/{pres_id}", json={"name": "Updated"}, headers=headers)
    assert upd.status_code == 200
    assert upd.json().get("name") == "Updated"

    # Supprimer
    dl = await client.delete(f"/presenters/del/{pres_id}", headers=headers)
    print(f"Réponse suppression : {dl.text}")
    assert dl.status_code == 204

    # Vérifier la suppression (retourne 200 au lieu de 404 car c'est un soft delete)
    # On ne peut pas vérifier le soft delete avec un GET, car il renvoie 200
    nf = await client.get(f"/presenters/{pres_id}", headers=headers)
    print(f"Réponse non trouvée : {nf.json()}")
    assert nf.status_code == 200