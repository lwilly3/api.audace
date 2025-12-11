# 🔧 Variables d'Environnement

Guide complet de toutes les variables d'environnement utilisées par l'API Audace.

---

## 📋 Vue d'ensemble

L'application utilise des variables d'environnement pour configurer :
- Base de données PostgreSQL
- Authentification JWT
- Configuration email
- URLs frontend/backend
- **Credentials de l'admin par défaut**
- Paramètres d'exécution

---

## 🗄️ Base de Données PostgreSQL

### Variables requises

| Variable | Type | Description | Exemple |
|----------|------|-------------|---------|
| `POSTGRES_DB` | string | Nom de la base de données | `audace_db` |
| `POSTGRES_USER` | string | Utilisateur PostgreSQL | `audace_user` |
| `POSTGRES_PASSWORD` | string | **⚠️ OBLIGATOIRE** Mot de passe | `MotDePasseSecurise123!` |
| `POSTGRES_PORT` | int | Port PostgreSQL | `5432` (défaut) |

### Configuration dans le code

```python
# app/config/config.py
DATABASE_HOSTNAME = os.getenv("DATABASE_HOSTNAME", "localhost")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_USERNAME = os.getenv("DATABASE_USERNAME", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME", "audace_db")
```

### Docker Compose

```yaml
services:
  db:
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-audace_db}
      POSTGRES_USER: ${POSTGRES_USER:-audace_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  
  api:
    environment:
      DATABASE_HOSTNAME: db
      DATABASE_PORT: 5432
      DATABASE_USERNAME: ${POSTGRES_USER:-audace_user}
      DATABASE_PASSWORD: ${POSTGRES_PASSWORD}
      DATABASE_NAME: ${POSTGRES_DB:-audace_db}
```

---

## 🔐 JWT & Sécurité

### Variables requises

| Variable | Type | Description | Valeur par défaut |
|----------|------|-------------|-------------------|
| `SECRET_KEY` | string | **⚠️ OBLIGATOIRE** Clé secrète JWT | Aucune |
| `ALGORITHM` | string | Algorithme de chiffrement | `HS256` |
| `ACCESS_TOKEN_EXPIRATION_MINUTE` | int | Durée validité token (minutes) | `30` |

### Génération de SECRET_KEY

```bash
# Méthode recommandée
openssl rand -hex 32

# Résultat exemple
a3f5e8d2c9b1a7f4e6d8c2b5a9f7e3d1c8b4a6f2e9d7c5b3a1f8e6d4c2b9a7f5
```

### ⚠️ Sécurité

- **Ne JAMAIS committer** `SECRET_KEY` dans git
- Utiliser une clé **différente** pour dev/staging/production
- Changer la clé = invalidation de tous les tokens existants

### Configuration dans le code

```python
# app/config/config.py
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRATION_MINUTE", "30"))
```

---

## 👤 Admin par Défaut (Nouveau ✨)

### Variables pour l'admin automatique

Au **premier démarrage**, un utilisateur admin est automatiquement créé avec ces credentials :

| Variable | Type | Description | Valeur par défaut |
|----------|------|-------------|-------------------|
| `ADMIN_USERNAME` | string | Nom d'utilisateur admin | `admin` |
| `ADMIN_PASSWORD` | string | Mot de passe admin | `Admin@2024!` |
| `ADMIN_EMAIL` | string | Email admin | `admin@audace.local` |
| `ADMIN_NAME` | string | Prénom admin | `Administrateur` |
| `ADMIN_FAMILY_NAME` | string | Nom de famille admin | `Système` |

### ⚠️ Sécurité - IMPORTANT

**En production, vous DEVEZ personnaliser ces variables !**

Les valeurs par défaut sont **publiques** dans le code source. Ne les utilisez JAMAIS en production.

### Configuration recommandée

#### Dans Dokploy (Production)

```
ADMIN_USERNAME=votre_admin
ADMIN_PASSWORD=MotDePasseTresFort2024!@#
ADMIN_EMAIL=admin@votre-domaine.com
ADMIN_NAME=Jean
ADMIN_FAMILY_NAME=Dupont
```

#### Dans docker-compose.yml

Les variables sont déjà configurées pour récupérer les valeurs de Dokploy :

```yaml
api:
  environment:
    # Admin par défaut (créé automatiquement au démarrage)
    ADMIN_USERNAME: ${ADMIN_USERNAME:-admin}
    ADMIN_PASSWORD: ${ADMIN_PASSWORD:-Admin@2024!}
    ADMIN_EMAIL: ${ADMIN_EMAIL:-admin@audace.local}
    ADMIN_NAME: ${ADMIN_NAME:-Administrateur}
    ADMIN_FAMILY_NAME: ${ADMIN_FAMILY_NAME:-Système}
```

### Vérification des variables

#### Via l'API

```bash
curl https://api.cloud.audace.ovh/setup/env-check
```

Réponse :
```json
{
  "environment_variables": {
    "ADMIN_USERNAME": {
      "defined": true,
      "value": "votre_admin",
      "source": "environment"  // ✅ Variable personnalisée
    },
    "ADMIN_PASSWORD": {
      "defined": true,
      "value": "***MASKED***",
      "source": "environment"
    }
  }
}
```

- `"source": "environment"` = ✅ Votre variable personnalisée est utilisée
- `"source": "default"` = ⚠️ Valeur par défaut utilisée (à éviter en prod)

#### Via les logs

Au démarrage, les logs montrent :

```
🔍 Lecture des variables d'environnement...
📋 Variables d'environnement détectées:
   - ADMIN_USERNAME: ✅ défini
   - ADMIN_PASSWORD: ✅ défini
   - ADMIN_EMAIL: ✅ défini
   - ADMIN_NAME: ✅ défini
   - ADMIN_FAMILY_NAME: ✅ défini
Credentials qui seront utilisés:
   - Username: votre_admin
   - Email: admin@votre-domaine.com
```

### Comportement

1. **Premier démarrage** :
   - ✅ Admin créé automatiquement avec les credentials configurés
   - ✅ Toutes les permissions activées
   - ✅ Rôle "Admin" assigné

2. **Redémarrage ultérieur** :
   - ℹ️ Admin détecté, aucune création
   - ℹ️ Variables ignorées (admin déjà existant)

3. **Si variables non définies** :
   - ⚠️ Utilise les valeurs par défaut (non sécurisé en production)
   - 📝 Log : `"❌ non défini (valeur par défaut)"`

### Configuration dans le code

```python
# app/db/init_admin.py
async def create_default_admin(db: Session) -> None:
    # Lecture des variables d'environnement
    default_username = os.getenv("ADMIN_USERNAME", "admin")
    default_password = os.getenv("ADMIN_PASSWORD", "Admin@2024!")
    default_email = os.getenv("ADMIN_EMAIL", "admin@audace.local")
    default_name = os.getenv("ADMIN_NAME", "Administrateur")
    default_family_name = os.getenv("ADMIN_FAMILY_NAME", "Système")
    
    # Log pour debug
    logger.info("🔍 Lecture des variables d'environnement...")
    logger.info("📋 Variables d'environnement détectées:")
    logger.info(f"   - ADMIN_USERNAME: {'✅ défini' if os.getenv('ADMIN_USERNAME') else '❌ non défini (valeur par défaut)'}")
    # ...
```

---

## 📧 Configuration Email

### Variables pour l'envoi d'emails

Utilisé pour :
- Réinitialisation de mot de passe
- Invitations d'utilisateurs
- Notifications par email

| Variable | Type | Description | Exemple |
|----------|------|-------------|---------|
| `MAIL_USERNAME` | string | Adresse email expéditeur | `noreply@audace.com` |
| `MAIL_PASSWORD` | string | Mot de passe email | `app_password_xxx` |
| `MAIL_FROM` | string | Email "From" header | `noreply@audace.com` |
| `MAIL_PORT` | int | Port SMTP | `587` (TLS) ou `465` (SSL) |
| `MAIL_SERVER` | string | Serveur SMTP | `smtp.gmail.com` |
| `MAIL_FROM_NAME` | string | Nom affiché expéditeur | `Audace API` |
| `MAIL_TLS` | boolean | Utiliser TLS | `true` |
| `MAIL_SSL` | boolean | Utiliser SSL | `false` |

### Configuration Gmail

1. **Activer l'authentification à 2 facteurs** sur votre compte Google
2. **Créer un mot de passe d'application** :
   - Compte Google → Sécurité → Validation en 2 étapes
   - → Mots de passe des applications
   - → Sélectionner "Autre" → Nommer "Audace API"
3. Utiliser ce mot de passe dans `MAIL_PASSWORD`

```env
MAIL_USERNAME=votre.email@gmail.com
MAIL_PASSWORD=abcd efgh ijkl mnop  # Mot de passe d'application
MAIL_FROM=noreply@audace.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_TLS=true
MAIL_SSL=false
```

---

## 🌐 URLs de l'Application

### Variables requises

| Variable | Type | Description | Exemple |
|----------|------|-------------|---------|
| `FRONTEND_URL` | string | URL du frontend | `https://app.cloud.audace.ovh` |
| `BACKEND_URL` | string | URL de l'API | `https://api.cloud.audace.ovh` |

### Utilisation

- **CORS** : `FRONTEND_URL` est ajouté aux origines autorisées
- **Emails** : Liens dans les emails de reset password
- **Redirections** : Après validation de token

```python
# Exemple dans un email de reset password
reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
```

---

## 🚀 Environnement et Déploiement

### Variables d'environnement

| Variable | Type | Description | Valeurs possibles |
|----------|------|-------------|-------------------|
| `ENVIRONMENT` | string | Type d'environnement | `development`, `staging`, `production` |
| `DEBUG` | boolean | Mode debug | `true`, `false` |
| `WORKERS` | int | Nombre de workers Gunicorn | `4` (production), `1` (dev) |
| `HOST` | string | Host de l'API | `0.0.0.0` |
| `PORT` | int | Port de l'API | `8000` |

### Recommandations par environnement

#### Development
```env
ENVIRONMENT=development
DEBUG=true
WORKERS=1
```

#### Staging
```env
ENVIRONMENT=staging
DEBUG=false
WORKERS=2
```

#### Production
```env
ENVIRONMENT=production
DEBUG=false
WORKERS=4
```

---

## 📁 Fichiers de Configuration

### .env (local)

Créez un fichier `.env` à la racine :

```bash
# Ne JAMAIS committer ce fichier !
# Ajoutez .env dans .gitignore

POSTGRES_PASSWORD=dev_password
SECRET_KEY=dev_secret_key_xxx
ADMIN_USERNAME=admin_dev
ADMIN_PASSWORD=DevPassword123!
MAIL_USERNAME=test@example.com
MAIL_PASSWORD=test_password
```

### .env.example

Template pour les autres développeurs :

```bash
# Copiez ce fichier en .env et remplissez les valeurs

POSTGRES_PASSWORD=changeme
SECRET_KEY=generate_with_openssl_rand_hex_32
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@2024!
# ... autres variables
```

### docker-compose.yml

Utilise les variables `.env` ou de l'environnement :

```yaml
services:
  api:
    environment:
      # Syntaxe : ${VARIABLE_ENV:-valeur_par_defaut}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Obligatoire, pas de défaut
      ALGORITHM: ${ALGORITHM:-HS256}           # Optionnel, défaut = HS256
```

---

## 🔍 Diagnostic et Debug

### Vérifier les variables chargées

#### Endpoint de debug

```bash
GET /setup/env-check
```

Retourne l'état de toutes les variables `ADMIN_*` :

```json
{
  "environment_variables": {
    "ADMIN_USERNAME": {
      "defined": true,
      "value": "admin",
      "source": "environment"
    }
  }
}
```

#### Logs au démarrage

```
🔍 Lecture des variables d'environnement...
📋 Variables d'environnement détectées:
   - ADMIN_USERNAME: ✅ défini
   - ADMIN_PASSWORD: ❌ non défini (valeur par défaut)
```

### Problèmes courants

#### ❌ Variables non chargées dans Docker

**Symptôme** : `"source": "default"` dans `/setup/env-check`

**Causes possibles** :
1. Variables non définies dans Dokploy
2. Variables non transmises dans `docker-compose.yml`
3. Conteneur pas redémarré après modification

**Solution** :
```bash
# 1. Vérifier docker-compose.yml
grep -A 5 "ADMIN_USERNAME" docker-compose.yml

# 2. Redéployer complètement
docker-compose down
docker-compose up -d

# 3. Vérifier les variables dans le conteneur
docker exec audace_api env | grep ADMIN
```

#### ❌ SECRET_KEY non défini

**Erreur** : Application ne démarre pas

**Solution** :
```bash
# Générer une clé
openssl rand -hex 32

# Ajouter dans Dokploy ou .env
SECRET_KEY=votre_cle_generee
```

---

## 📚 Références

### Documentation liée

- [FIRST_LOGIN.md](../../FIRST_LOGIN.md) - Configuration admin par défaut
- [SETUP_ADMIN_ROUTE.md](../../SETUP_ADMIN_ROUTE.md) - Routes de diagnostic
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Guide de déploiement
- [.env.example](../../.env.example) - Template de configuration

### Ressources externes

- [FastAPI Settings Management](https://fastapi.tiangolo.com/advanced/settings/)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [12-Factor App Config](https://12factor.net/config)

---

## ✅ Checklist de Configuration

### Développement Local

- [ ] Fichier `.env` créé
- [ ] `POSTGRES_PASSWORD` défini
- [ ] `SECRET_KEY` généré
- [ ] Variables `ADMIN_*` personnalisées (optionnel)

### Production (Dokploy)

- [ ] `POSTGRES_PASSWORD` fort défini
- [ ] `SECRET_KEY` unique généré
- [ ] Variables `ADMIN_*` personnalisées **obligatoire**
- [ ] Configuration email complète (si utilisée)
- [ ] `FRONTEND_URL` et `BACKEND_URL` corrects
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] Variables vérifiées avec `/setup/env-check`
- [ ] Admin créé avec credentials personnalisés
- [ ] Mot de passe admin changé après première connexion

---

**Date de mise à jour** : 11 décembre 2025  
**Version** : 1.0.0
