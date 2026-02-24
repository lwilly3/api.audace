import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session
import uuid

from app.models import UserPermissions
from app.models.model_role import Role
from app.models.model_user_role import UserRole


# Marque le test comme asynchrone (nécessite pytest-asyncio)
@pytest.mark.asyncio
async def test_create_get_update_delete_user(client: AsyncClient, db: Session):
    # Générer un email unique pour éviter les conflits dans la base de données
    email = f"user_{uuid.uuid4().hex}@example.com"
    password = "TestPass123!"

    # ➤ 1. Inscription de l'utilisateur cible
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

    # ➤ 5. Créer un admin avec hierarchie supérieure pour pouvoir supprimer
    admin_email = f"admin_{uuid.uuid4().hex}@example.com"
    admin_signup = await client.post(
        "/auth/signup",
        json={"email": admin_email, "password": password}
    )
    assert admin_signup.status_code == 201
    admin_id = admin_signup.json().get("id")

    # Donner un rôle avec hierarchy_level élevé à l'admin via DB
    admin_role = Role(name=f"test_admin_{uuid.uuid4().hex[:6]}", hierarchy_level=100)
    db.add(admin_role)
    db.commit()
    db.refresh(admin_role)

    db.add(UserRole(user_id=admin_id, role_id=admin_role.id))
    db.commit()

    # Connexion de l'admin
    admin_login = await client.post(
        "/auth/login",
        data={"username": admin_email, "password": password}
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json().get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # ➤ 6. Suppression de l'utilisateur par l'admin
    delete_resp = await client.delete(f"/users/del/{user_id}", headers=admin_headers)
    # Vérifie que la suppression a renvoyé un code 204 (No Content)
    assert delete_resp.status_code == 204
    # Vérifie que la réponse contient le message attendu
    assert delete_resp.json() == {"detail": "User soft-deleted successfully"}

    # ➤ 7. Vérification que l'utilisateur n'existe plus
    get_after_delete = await client.get(f"/users/users/{user_id}", headers=admin_headers)
    # On s'attend maintenant à un code 404 (utilisateur introuvable)
    assert get_after_delete.status_code == 404

    # Nettoyage : supprimer le rôle et l'admin de test
    db.query(UserRole).filter(UserRole.user_id == admin_id).delete()
    db.query(Role).filter(Role.id == admin_role.id).delete()
    db.commit()
