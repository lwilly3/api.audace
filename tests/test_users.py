import pytest
from httpx import AsyncClient
import uuid

# Marque le test comme asynchrone (nécessite pytest-asyncio)
@pytest.mark.asyncio
async def test_create_get_update_delete_user(client: AsyncClient):
    # Générer un email unique pour éviter les conflits dans la base de données
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "TestPass123!"

    # ➤ 1. Inscription de l'utilisateur
    signup_resp = await client.post(
        "/auth/signup",
        json={"email": email, "password": password}
    )
    # Vérifie que l'inscription renvoie un code 201 (créé avec succès)
    assert signup_resp.status_code == 201, f"Signup failed: {signup_resp.text}"
    # Récupération de l'ID utilisateur à partir de la réponse
    user_data = signup_resp.json()
    user_id = user_data.get("id")

    # ➤ 2. Connexion de l'utilisateur pour obtenir un token JWT
    login_resp = await client.post(
        "/auth/login",
        data={"username": email, "password": password}
    )
    # Vérifie que la connexion a réussi
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    # Récupération du token d'accès
    token = login_resp.json().get("access_token")
    # Préparation de l'en-tête d'autorisation
    headers = {"Authorization": f"Bearer {token}"}

    # ➤ 3. Récupération des informations de l'utilisateur
    get_resp = await client.get(f"/users/users/{user_id}", headers=headers)
    # Vérifie que la récupération a réussi
    assert get_resp.status_code == 200
    # Vérifie que l'email retourné correspond à celui utilisé à l'inscription
    assert get_resp.json().get("email") == email

    # ➤ 4. Mise à jour du nom de l'utilisateur
    new_name = "UpdatedName"
    update_resp = await client.put(
        f"/users/updte/{user_id}",
        json={"name": new_name},
        headers=headers
    )
    # Vérifie que la mise à jour a réussi
    assert update_resp.status_code == 200
    # Vérifie que le nom a bien été mis à jour
    assert update_resp.json().get("name") == new_name

    # ➤ 5. Suppression de l'utilisateur
    delete_resp = await client.delete(f"/users/del/{user_id}", headers=headers)
    # Vérifie que la suppression a renvoyé un code 204 (No Content)
    assert delete_resp.status_code == 204
    # Vérifie que la réponse est vide (comme attendu pour une suppression 204)
    assert delete_resp.json() == {"detail": "User soft-deleted successfully"}

    # ➤ 6. Vérification que l'utilisateur n'existe plus
    get_after_delete = await client.get(f"/users/users/{user_id}", headers=headers)
    # On s'attend maintenant à un code 404 (utilisateur introuvable)
    assert get_after_delete.status_code == 404
