# 🔐 Première connexion - Guide d'installation

## Utilisateur Admin par défaut

Lors du **premier démarrage** de l'application, un utilisateur administrateur est automatiquement créé s'il n'existe pas déjà.

### Credentials par défaut

Par défaut (si aucune variable d'environnement n'est configurée) :

```
Username: admin
Password: Admin@2024!
Email: admin@audace.local
```

### ⚠️ IMPORTANT - Sécurité

**Ces credentials par défaut doivent être changés IMMÉDIATEMENT après la première connexion en production !**

## Configuration personnalisée

Vous pouvez personnaliser les credentials de l'admin par défaut en définissant ces variables d'environnement **AVANT** le premier démarrage :

### Option 1 : Via Dokploy (Recommandé)

Dans l'interface Dokploy, ajoutez les variables d'environnement :

```
ADMIN_USERNAME=votre_username
ADMIN_PASSWORD=VotreMotDePasseSecurise123!
ADMIN_EMAIL=admin@votre-domaine.com
ADMIN_NAME=Prénom
ADMIN_FAMILY_NAME=Nom
```

**Important** : Ces variables sont **déjà configurées** dans le `docker-compose.yml` et seront automatiquement transmises au conteneur.

### Option 2 : Via fichier .env local

```bash
# Créez un fichier .env à la racine du projet
ADMIN_USERNAME=votre_username
ADMIN_PASSWORD=VotreMotDePasseSecurise123!
ADMIN_EMAIL=admin@votre-domaine.com
ADMIN_NAME=Prénom
ADMIN_FAMILY_NAME=Nom
```

### Option 3 : Modifier directement docker-compose.yml

Dans la section `api.environment`, modifiez les valeurs par défaut :

```yaml
# Admin par défaut
ADMIN_USERNAME: ${ADMIN_USERNAME:-votre_username}
ADMIN_PASSWORD: ${ADMIN_PASSWORD:-VotreMotDePasse123!}
ADMIN_EMAIL: ${ADMIN_EMAIL:-admin@votre-domaine.com}
ADMIN_NAME: ${ADMIN_NAME:-Prénom}
ADMIN_FAMILY_NAME: ${ADMIN_FAMILY_NAME:-Nom}
```

## Processus de première connexion

### 1. Démarrer l'application

```bash
# Avec Docker
docker-compose up -d

# Ou directement
uvicorn maintest:app --host 0.0.0.0 --port 8000
```

### 2. Vérifier que les variables d'environnement sont chargées

#### Via l'API (Recommandé)

Après le démarrage, vérifiez que vos variables personnalisées sont bien chargées :

```bash
curl https://api.cloud.audace.ovh/setup/env-check
```

**Réponse attendue avec variables personnalisées :**
```json
{
  "environment_variables": {
    "ADMIN_USERNAME": {
      "defined": true,
      "value": "votre_username",
      "source": "environment"
    },
    "ADMIN_PASSWORD": {
      "defined": true,
      "value": "***MASKED***",
      "source": "environment"
    },
    "ADMIN_EMAIL": {
      "defined": true,
      "value": "admin@votre-domaine.com",
      "source": "environment"
    },
    ...
  },
  "help": "Les variables avec 'source: environment' sont définies. Les autres utilisent les valeurs par défaut."
}
```

✅ Si `"source": "environment"` → Vos variables personnalisées sont utilisées
❌ Si `"source": "default"` → Les valeurs par défaut sont utilisées (vérifiez votre config Dokploy)

#### Via les logs Docker

Lors du démarrage, vous devriez voir dans les logs :

```
🚀 Démarrage de l'application - Vérification de l'admin par défaut...
🔍 Lecture des variables d'environnement...
📋 Variables d'environnement détectées:
   - ADMIN_USERNAME: ✅ défini
   - ADMIN_PASSWORD: ✅ défini
   - ADMIN_EMAIL: ✅ défini
   - ADMIN_NAME: ✅ défini
   - ADMIN_FAMILY_NAME: ✅ défini
Credentials qui seront utilisés:
   - Username: votre_username
   - Email: admin@votre-domaine.com
✅ Utilisateur admin créé avec succès!
   - Username: votre_username
   - Email: admin@votre-domaine.com
   ⚠️  IMPORTANT: Changez le mot de passe par défaut dès la première connexion!
✅ Initialisation de l'admin terminée
```

Ou si un admin existe déjà :

```
🚀 Démarrage de l'application - Vérification de l'admin par défaut...
1 utilisateur(s) admin trouvé(s). Pas besoin de créer un admin par défaut.
✅ Initialisation de l'admin terminée
```

### 3. Se connecter pour la première fois

#### Via Swagger UI (Recommandé pour les tests)

1. Ouvrez votre navigateur : `https://api.cloud.audace.ovh/docs` (ou `http://localhost:8000/docs`)
2. Cliquez sur **"Authorize"** en haut à droite (icône cadenas 🔒)
3. Dans le formulaire OAuth2, entrez :
   - **username** : `admin`
   - **password** : `Admin@2024!` (ou votre mot de passe personnalisé)
4. Cliquez sur **"Authorize"**
5. Vous êtes maintenant authentifié !

#### Via cURL

```bash
curl -X POST "https://api.cloud.audace.ovh/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin@2024!"
```

Réponse attendue :

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Via une application frontend

```javascript
// Exemple avec fetch
const response = await fetch('https://api.cloud.audace.ovh/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    username: 'admin',
    password: 'Admin@2024!'
  })
});

const data = await response.json();
const token = data.access_token;

// Utiliser le token pour les requêtes suivantes
const protectedResponse = await fetch('https://api.cloud.audace.ovh/users', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 4. Changer le mot de passe (OBLIGATOIRE en production)

Une fois connecté, changez immédiatement le mot de passe :

#### Via Swagger UI

1. Trouvez l'endpoint **PUT** `/users/{user_id}`
2. Utilisez votre ID utilisateur (généralement `1` pour le premier admin)
3. Dans le body, envoyez :
```json
{
  "password": "VotreNouveauMotDePasseSecurise123!"
}
```

#### Via cURL

```bash
# D'abord, récupérer votre ID utilisateur
curl -X GET "https://api.cloud.audace.ovh/users/me" \
  -H "Authorization: Bearer VOTRE_TOKEN"

# Puis changer le mot de passe
curl -X PUT "https://api.cloud.audace.ovh/users/1" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"password": "VotreNouveauMotDePasseSecurise123!"}'
```

## Création d'autres utilisateurs admin

Une fois connecté en tant qu'admin, vous pouvez créer d'autres utilisateurs et leur assigner le rôle Admin :

### 1. Créer un nouvel utilisateur

```bash
POST /users
{
  "username": "nouvel_admin",
  "name": "Jean",
  "family_name": "Dupont",
  "email": "jean.dupont@audace.com",
  "password": "MotDePasseSecurise123!"
}
```

### 2. Assigner le rôle Admin

```bash
POST /users/{user_id}/roles
{
  "role_ids": [1]  # ID du rôle Admin (généralement 1)
}
```

### 3. Activer toutes les permissions

```bash
PUT /permissions/users/{user_id}
{
  "can_view_users": true,
  "can_create_users": true,
  "can_edit_users": true,
  "can_delete_users": true,
  "can_manage_permissions": true,
  // ... toutes les autres permissions à true
}
```

## Récupération en cas de perte du mot de passe admin

Si vous perdez le mot de passe de tous les admins, vous avez deux options :

### Option 1 : Utiliser la fonctionnalité de reset password

1. Utilisez l'endpoint `/auth/forgot-password` avec l'email de l'admin
2. Un token de réinitialisation sera créé dans la base de données
3. Récupérez le token directement depuis la base de données :
```sql
SELECT token FROM password_reset_tokens 
WHERE user_id = (SELECT id FROM users WHERE username = 'admin')
ORDER BY created_at DESC LIMIT 1;
```
4. Utilisez ce token avec l'endpoint `/auth/reset-password`

### Option 2 : Réinitialiser via la base de données (Méthode d'urgence)

```sql
-- Connectez-vous à votre base PostgreSQL
psql -U audace_user -d audace_db

-- Générer un hash pour un nouveau mot de passe
-- Le hash ci-dessous correspond à "NewAdmin2024!"
UPDATE users 
SET password = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND/qhpkhf3Hy'
WHERE username = 'admin';
```

Ou utilisez ce script Python pour générer un nouveau hash :

```python
from app.utils.hash import hash_password

new_password = "VotreNouveauMotDePasse123!"
hashed = hash_password(new_password)
print(f"Hash: {hashed}")

# Ensuite, mettez à jour manuellement dans la BD avec ce hash
```

### Option 3 : Redémarrer avec un nouvel admin (Dernier recours)

Si vraiment bloqué, vous pouvez :

1. **Supprimer TOUS les utilisateurs admin** de la base de données :
```sql
-- ⚠️ ATTENTION: Ceci supprime tous les admins existants !
DELETE FROM user_roles WHERE role_id = (SELECT id FROM roles WHERE name = 'Admin');
```

2. **Redémarrer l'application** : Un nouvel admin par défaut sera automatiquement créé

3. **Configurer les credentials** avant le redémarrage via les variables d'environnement

## Vérification de l'état de l'admin

Pour vérifier si l'admin existe et fonctionne :

```bash
# Vérifier la présence de l'admin dans la base de données
psql -U audace_user -d audace_db -c "
SELECT u.id, u.username, u.email, u.is_active, r.name as role
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE r.name = 'Admin' AND u.is_deleted = false;
"
```

Résultat attendu :
```
 id | username |        email         | is_active |  role
----+----------+----------------------+-----------+-------
  1 | admin    | admin@audace.local  | t         | Admin
```

## Questions fréquentes (FAQ)

### Q: L'admin n'est pas créé au démarrage, pourquoi ?

**R:** Vérifiez que :
1. La connexion à la base de données fonctionne
2. Le rôle "Admin" existe dans la table `roles`
3. Les logs ne montrent pas d'erreurs
4. Les migrations Alembic ont été appliquées : `alembic upgrade head`

### Q: Puis-je personnaliser les permissions de l'admin par défaut ?

**R:** Oui, modifiez la fonction `create_admin_permissions()` dans `app/db/init_admin.py`.

### Q: Que se passe-t-il si je change les variables d'environnement après le premier démarrage ?

**R:** Les variables d'environnement ne sont utilisées que lors de la **création initiale** de l'admin. Si un admin existe déjà, les nouvelles valeurs sont ignorées.

### Q: Comment désactiver la création automatique de l'admin ?

**R:** Commentez la fonction `initialize_default_admin()` dans `maintest.py`, mais ce n'est **pas recommandé** en production.

### Q: L'admin a toutes les permissions mais ne peut rien faire ?

**R:** Vérifiez que :
1. Le token JWT est valide et non expiré
2. Les permissions sont bien dans la table `user_permissions`
3. Le rôle "Admin" est assigné dans `user_roles`

```sql
-- Vérifier les permissions de l'admin
SELECT * FROM user_permissions WHERE user_id = 1;

-- Vérifier les rôles de l'admin
SELECT u.username, r.name 
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.id = 1;
```

## Support

Pour toute question ou problème :
- Consultez les logs de l'application : `docker-compose logs -f` ou `tail -f api_logs.log`
- Vérifiez la documentation complète : `docs/README.md`
- Contactez l'équipe de développement

---

**Rappel de sécurité** : 🔐
- ✅ Changez TOUJOURS les credentials par défaut en production
- ✅ Utilisez des mots de passe forts (12+ caractères, majuscules, minuscules, chiffres, symboles)
- ✅ Activez l'authentification à deux facteurs si disponible
- ✅ Ne partagez JAMAIS les credentials admin
- ✅ Utilisez des variables d'environnement, pas de valeurs hardcodées
