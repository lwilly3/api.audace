import pytest
import random
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_signup_and_login(client: AsyncClient):
    # Générer un email unique pour éviter les conflits
    email = f"test{random.randint(1000, 9999)}@example.com"
    password = "Pass1234!"

    # Inscription
    signup_resp = await client.post(
        "/auth/signup",
        json={"email": email, "password": password}
    )
    assert signup_resp.status_code == 201
    data = signup_resp.json()
    assert data.get("email") == email
    assert data.get("is_active") is True

    # Connexion (OAuth2 form-data)
    login_resp = await client.post(
        "/auth/login",
        data={"username": email, "password": password}
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert tokens.get("token_type") == "bearer"

    # Test avec mot de passe incorrect
    bad_login = await client.post(
        "/auth/login",
        data={"username": email, "password": "wrongpass"}
    )
    assert bad_login.status_code == 403
    assert "access_token" not in bad_login.json()
