# 🔍 Debug - Vérification de la création de l'admin

## Problème résolu

Le code a été corrigé pour :
1. ✅ Utiliser les vrais noms de champs de permissions (ex: `can_acces_showplan_section`)
2. ✅ Utiliser la fonction `initialize_user_permissions` du CRUD
3. ✅ Ajouter un logging détaillé étape par étape
4. ✅ Afficher clairement les credentials créés

## Comment vérifier que l'admin est créé

### Option 1: Via les logs Docker

```bash
# Voir les logs en temps réel
docker logs -f <nom_du_conteneur>

# Ou avec docker-compose
docker-compose logs -f

# Chercher les lignes spécifiques
docker logs <nom_du_conteneur> 2>&1 | grep -A 20 "Initialisation de l'utilisateur"
```

**Ce que vous devriez voir dans les logs :**

```
============================================================
Initialisation de l'utilisateur administrateur par défaut
============================================================
Étape 1/5: Vérification du rôle 'Admin'...
✅ Rôle 'Admin' créé avec succès (ID: 1)
Étape 2/5: Recherche d'utilisateurs admin existants...
⚠️  Aucun utilisateur admin trouvé dans la base de données!
Étape 3/5: Création de l'admin par défaut...
Credentials utilisés:
   - Username: admin
   - Email: admin@audace.local
   - Name: Administrateur Système
Création du nouvel utilisateur admin...
✅ Utilisateur créé avec ID: 1
Assignation du rôle Admin...
✅ Rôle Admin assigné
Étape 4/5: Initialisation des permissions...
✅ Permissions initialisées
Étape 5/5: Activation de toutes les permissions admin...
✅ Toutes les permissions admin activées pour l'utilisateur 1

============================================================
✅ UTILISATEUR ADMIN CRÉÉ AVEC SUCCÈS!
============================================================
Username: admin
Password: Admin@2024!
Email: admin@audace.local
User ID: 1
============================================================
⚠️  IMPORTANT: Changez le mot de passe par défaut dès la première connexion!
⚠️  Mot de passe par défaut utilisé. Définissez ADMIN_PASSWORD dans les variables d'environnement pour plus de sécurité.
============================================================
```

### Option 2: Via la base de données PostgreSQL

```bash
# Se connecter à PostgreSQL
docker exec -it <nom_conteneur_postgres> psql -U audace_user -d audace_db

# Ou directement
psql -h localhost -U audace_user -d audace_db
```

**Requêtes SQL pour vérifier :**

```sql
-- 1. Vérifier que le rôle Admin existe
SELECT * FROM roles WHERE name = 'Admin';

-- 2. Vérifier les utilisateurs admin
SELECT u.id, u.username, u.email, u.is_active, u.is_deleted, u.created_at
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE r.name = 'Admin' AND u.is_deleted = false;

-- 3. Vérifier les permissions de l'admin
SELECT * FROM user_permissions WHERE user_id = 1;

-- 4. Compter les permissions activées
SELECT 
    user_id,
    (can_acces_showplan_section::int + 
     can_acces_users_section::int + 
     can_acces_guests_section::int + 
     can_acces_presenters_section::int + 
     can_acces_emissions_section::int +
     can_create_showplan::int +
     can_edit_showplan::int +
     can_view_users::int +
     can_manage_roles::int) as permissions_actives
FROM user_permissions 
WHERE user_id = 1;
```

### Option 3: Via l'API (Swagger)

1. Redéployer votre conteneur :
```bash
docker-compose down
docker-compose up -d
```

2. Attendre quelques secondes que l'app démarre

3. Aller sur Swagger : `https://api.cloud.audace.ovh/docs`

4. Tester le login :
   - Cliquer sur **"Authorize"** 🔒
   - Username: `admin`
   - Password: `Admin@2024!`
   - Cliquer **"Authorize"**

5. Si ça fonctionne, l'admin a été créé ! ✅

### Option 4: Via cURL

```bash
# Tester le login
curl -X POST "https://api.cloud.audace.ovh/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin@2024!"
```

**Réponse attendue si l'admin existe :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Réponse si l'admin n'existe pas :**
```json
{
  "detail": "Invalid credentials"
}
```

## Si l'admin n'est toujours pas créé

### 1. Vérifier que le lifespan s'exécute

Cherchez cette ligne dans les logs :
```
🚀 Démarrage de l'application - Vérification de l'admin par défaut...
```

Si cette ligne n'apparaît PAS, le lifespan ne s'exécute pas. Vérifiez :
- Le fichier `maintest.py` a bien la fonction `lifespan`
- L'app FastAPI est initialisée avec `lifespan=lifespan`

### 2. Vérifier les migrations Alembic

```bash
# Vérifier que toutes les migrations sont appliquées
docker exec -it <conteneur_app> alembic current

# Appliquer les migrations si nécessaire
docker exec -it <conteneur_app> alembic upgrade head
```

### 3. Vérifier les variables d'environnement

```bash
# Vérifier les variables dans le conteneur
docker exec -it <conteneur_app> env | grep ADMIN

# Ou dans docker-compose.yml
cat docker-compose.yml | grep -A 5 ADMIN
```

### 4. Forcer la recréation en supprimant tous les users

**⚠️ ATTENTION : Ceci supprime TOUS les utilisateurs !**

```sql
-- Se connecter à la base
docker exec -it <conteneur_postgres> psql -U audace_user -d audace_db

-- Supprimer tous les liens user_roles
DELETE FROM user_roles;

-- Supprimer toutes les permissions
DELETE FROM user_permissions;

-- Supprimer tous les utilisateurs
DELETE FROM users;

-- Redémarrer l'app
docker-compose restart
```

Après redémarrage, l'admin devrait être recréé automatiquement.

### 5. Tester manuellement le script

```bash
# Entrer dans le conteneur
docker exec -it <conteneur_app> bash

# Lancer le script de test
python scripts/test_admin_init.py
```

Ce script va :
- Vérifier l'état actuel
- Créer l'admin si nécessaire
- Tester le mot de passe
- Afficher tous les détails

## Logs d'erreur à chercher

Si vous voyez ces messages, voici ce qu'ils signifient :

### Erreur: "Rôle 'Admin' n'existe pas"
→ Le rôle sera créé automatiquement, pas d'inquiétude

### Erreur: "Un utilisateur avec le username 'admin' existe déjà"
→ L'utilisateur existe mais n'a pas le rôle Admin
→ Le script lui ajoute automatiquement le rôle

### Erreur: "Erreur SQL lors de la création"
→ Problème de connexion à la base de données
→ Vérifiez que PostgreSQL est démarré
→ Vérifiez DATABASE_URL dans les variables d'environnement

### Erreur: "Aucune permission trouvée pour l'utilisateur"
→ Les permissions n'ont pas été initialisées
→ Le script devrait les créer automatiquement

## Variables d'environnement personnalisées

Pour changer les credentials par défaut, ajoutez dans votre `.env` ou docker-compose.yml :

```bash
ADMIN_USERNAME=votre_admin
ADMIN_PASSWORD=VotreMotDePasseSecurise123!
ADMIN_EMAIL=admin@votre-domaine.com
ADMIN_NAME=Prénom
ADMIN_FAMILY_NAME=Nom
```

## Support

Si malgré tout l'admin n'est pas créé :

1. **Capturez les logs complets** :
```bash
docker-compose logs > logs_complets.txt
```

2. **Envoyez les logs** avec :
   - Les 100 premières lignes (démarrage)
   - Les lignes contenant "admin" ou "Admin"
   - Les lignes d'erreur (ERROR, ERREUR, ❌)

3. **Informations système** :
   - Version de Docker
   - Version de Python dans le conteneur
   - Version de PostgreSQL
   - Sortie de `alembic current`

---

**Dernière modification** : 11 décembre 2025  
**Commit** : fa18d23
