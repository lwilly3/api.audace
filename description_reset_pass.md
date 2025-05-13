# Réinitialisation de mot de passe

Cette fonctionnalité permet à un utilisateur de générer un token temporaire puis de réinitialiser son mot de passe.

---

## 1. Génération du token de réinitialisation

- NOUVEAU : `{ "user_id": 123 }`

**Endpoint** : `POST /auth/generate-reset-token`

**Description** :
- Vérifie que l’adresse email existe en base.
- Génère un JWT expirant au bout de 15 minutes (payload : `user_id`, `exp`, `purpose: password_reset`).

**Requête** :
```http
POST /auth/generate-reset-token HTTP/1.1
Content-Type: application/json

{
  "user_id": 123
}
```

**Réponse (200 OK)** :
```json
{
  "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...",
  "expires_at": "2025-05-13T14:22:00.123456"
}
```

**Erreurs** :
- `404 Not Found` si l’utilisateur n’existe pas.

---

## 2. Réinitialisation du mot de passe

**Endpoint** : `POST /auth/reset-password`

**Description** :
- Reçoit le token généré précédemment et le nouveau mot de passe.
- Vérifie la validité et l’expiration du token, ainsi que le champ `purpose`.
- Hache le nouveau mot de passe avec `utils.hash()` et met à jour l’utilisateur.

**Requête** :
```http
POST /auth/reset-password HTTP/1.1
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpX...",
  "new_password": "NouveauMotDePasse123!"
}
```

**Réponse (200 OK)** :
```json
{
  "message": "Mot de passe réinitialisé avec succès"
}
```

**Erreurs** :
- `400 Bad Request` si le token est invalide.
- `410 Gone` si le token est expiré.
- `404 Not Found` si l’utilisateur lié au token n’existe pas.

---

### Prérequis
- Installation de la dépendance JWT :
  ```bash
  pip install python-jose[cryptography]
  ```
- Variables d’environnement :
  - `SECRET_KEY` (clé secrète JWT)
  - `ALGORITHM` (algorithme de signature, ex. `HS256`)

---

*Document généré le 13 mai 2025.*