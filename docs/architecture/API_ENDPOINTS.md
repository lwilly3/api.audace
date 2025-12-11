# 🚀 Guide des endpoints API

Documentation complète de tous les endpoints disponibles dans l'API Audace.

---

## Table des matières

1. [Format des réponses](#format-des-réponses)
2. [Authentification](#authentification)
3. [Utilisateurs](#utilisateurs)
4. [Shows (Émissions)](#shows-émissions)
5. [Présentateurs](#présentateurs)
6. [Invités](#invités)
7. [Émissions](#émissions)
8. [Segments](#segments)
9. [Rôles](#rôles)
10. [Permissions](#permissions)
11. [Tableau de bord](#tableau-de-bord)
12. [Notifications](#notifications)
13. [Recherche](#recherche)
14. [Audit Logs](#audit-logs)

---

## 📋 Format des réponses

### Réponse standard de succès
```json
{
  "id": 1,
  "name": "Morning Show",
  "created_at": "2025-12-11T10:00:00",
  "updated_at": "2025-12-11T10:00:00"
}
```

### Réponse standard d'erreur
```json
{
  "detail": "Resource not found"
}
```

### Codes HTTP utilisés
| Code | Signification |
|------|---------------|
| 200 | Succès (GET, PUT) |
| 201 | Créé (POST) |
| 204 | Aucun contenu (DELETE) |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Non autorisé (permission) |
| 404 | Ressource introuvable |
| 409 | Conflit (ex: email déjà utilisé) |
| 422 | Validation échouée |
| 500 | Erreur serveur |

---

## 🔐 Authentification

**Base URL :** `/auth`

**Fichier :** `routeur/auth.py`

### POST /auth/signup
Créer un nouveau compte utilisateur.

**Body :**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Réponse (201) :**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2025-12-11T10:00:00"
}
```

**Erreurs :**
- `409` : Email déjà utilisé
- `422` : Email invalide ou mot de passe trop court

---

### POST /auth/login
Se connecter et obtenir un token JWT.

**Body :**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Réponse (200) :**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Erreurs :**
- `401` : Email ou mot de passe incorrect

**Utilisation du token :**
```bash
curl -H "Authorization: Bearer <access_token>" https://api.cloud.audace.ovh/users/me
```

---

### POST /auth/logout
Révoquer le token actuel.

**Headers :**
```
Authorization: Bearer <access_token>
```

**Réponse (200) :**
```json
{
  "message": "Successfully logged out"
}
```

---

### POST /auth/forgot-password
Demander un lien de réinitialisation de mot de passe.

**Body :**
```json
{
  "email": "user@example.com"
}
```

**Réponse (200) :**
```json
{
  "message": "Password reset email sent"
}
```

---

### POST /auth/reset-password
Réinitialiser le mot de passe avec un token.

**Body :**
```json
{
  "token": "abc123...",
  "new_password": "NewSecurePass123!"
}
```

**Réponse (200) :**
```json
{
  "message": "Password successfully reset"
}
```

**Erreurs :**
- `400` : Token invalide ou expiré
- `404` : Token introuvable

---

## 👥 Utilisateurs

**Base URL :** `/users`

**Fichier :** `routeur/users_route.py`

**Authentification :** Requise pour tous les endpoints

### GET /users/me
Obtenir les informations de l'utilisateur connecté.

**Headers :**
```
Authorization: Bearer <access_token>
```

**Réponse (200) :**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2025-12-11T10:00:00",
  "updated_at": "2025-12-11T10:00:00"
}
```

---

### GET /users
Lister tous les utilisateurs (pagination).

**Query params :**
- `skip` : Nombre à sauter (défaut: 0)
- `limit` : Nombre max (défaut: 100)

**Exemple :**
```bash
GET /users?skip=0&limit=20
```

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "email": "user1@example.com",
    "created_at": "2025-12-11T10:00:00"
  },
  {
    "id": 2,
    "email": "user2@example.com",
    "created_at": "2025-12-11T11:00:00"
  }
]
```

---

### GET /users/{user_id}
Obtenir un utilisateur par ID.

**Réponse (200) :**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2025-12-11T10:00:00",
  "updated_at": "2025-12-11T10:00:00"
}
```

**Erreurs :**
- `404` : Utilisateur introuvable

---

### PUT /users/{user_id}
Mettre à jour un utilisateur.

**Body :**
```json
{
  "email": "newemail@example.com"
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "email": "newemail@example.com",
  "updated_at": "2025-12-11T11:00:00"
}
```

---

### DELETE /users/{user_id}
Supprimer un utilisateur (soft delete).

**Réponse (204) :**
Aucun contenu.

---

## 📻 Shows (Émissions)

**Base URL :** `/shows`

**Fichier :** `routeur/show_route.py`

**Authentification :** Requise

### POST /shows
Créer un nouveau show.

**Body :**
```json
{
  "name": "Morning Show",
  "description": "Émission matinale avec infos et musique",
  "presenter_ids": [1, 2]
}
```

**Réponse (201) :**
```json
{
  "id": 1,
  "name": "Morning Show",
  "description": "Émission matinale avec infos et musique",
  "user_id": 5,
  "created_at": "2025-12-11T10:00:00",
  "presenters": [
    {
      "id": 1,
      "name": "Jean Dupont"
    },
    {
      "id": 2,
      "name": "Marie Martin"
    }
  ]
}
```

---

### GET /shows
Lister tous les shows (non supprimés).

**Query params :**
- `skip` : Offset (défaut: 0)
- `limit` : Limite (défaut: 100)

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "name": "Morning Show",
    "description": "...",
    "presenters": [...]
  },
  {
    "id": 2,
    "name": "Evening News",
    "description": "...",
    "presenters": [...]
  }
]
```

---

### GET /shows/{show_id}
Obtenir un show par ID.

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "Morning Show",
  "description": "...",
  "user_id": 5,
  "created_at": "2025-12-11T10:00:00",
  "presenters": [
    {
      "id": 1,
      "name": "Jean Dupont",
      "bio": "..."
    }
  ],
  "emissions": [
    {
      "id": 101,
      "title": "Morning Show - 11 Dec 2025",
      "date": "2025-12-11"
    }
  ]
}
```

---

### PUT /shows/{show_id}
Mettre à jour un show.

**Body :**
```json
{
  "name": "Good Morning Show",
  "description": "Nouvelle description",
  "presenter_ids": [1, 3]
}
```

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "Good Morning Show",
  "description": "Nouvelle description",
  "updated_at": "2025-12-11T11:00:00"
}
```

---

### DELETE /shows/{show_id}
Supprimer un show (soft delete).

**Réponse (204) :**
Aucun contenu.

---

## 🎤 Présentateurs

**Base URL :** `/presenters`

**Fichier :** `routeur/presenter_route.py`

**Authentification :** Requise

### POST /presenters
Créer un nouveau présentateur.

**Body :**
```json
{
  "name": "Jean Dupont",
  "bio": "Journaliste radio avec 10 ans d'expérience"
}
```

**Réponse (201) :**
```json
{
  "id": 1,
  "name": "Jean Dupont",
  "bio": "Journaliste radio avec 10 ans d'expérience",
  "user_id": 5,
  "created_at": "2025-12-11T10:00:00"
}
```

---

### GET /presenters
Lister tous les présentateurs.

**Query params :**
- `skip`, `limit`

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "name": "Jean Dupont",
    "bio": "..."
  },
  {
    "id": 2,
    "name": "Marie Martin",
    "bio": "..."
  }
]
```

---

### GET /presenters/{presenter_id}
Obtenir un présentateur par ID.

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "Jean Dupont",
  "bio": "...",
  "shows": [
    {
      "id": 1,
      "name": "Morning Show"
    }
  ]
}
```

---

### PUT /presenters/{presenter_id}
Mettre à jour un présentateur.

**Body :**
```json
{
  "name": "Jean-Pierre Dupont",
  "bio": "Nouvelle bio"
}
```

---

### DELETE /presenters/{presenter_id}
Supprimer un présentateur (soft delete).

**Réponse (204) :**
Aucun contenu.

---

## 👔 Invités

**Base URL :** `/guests`

**Fichier :** `routeur/guest_route.py`

**Authentification :** Requise

### POST /guests
Créer un nouvel invité.

**Body :**
```json
{
  "name": "Dr. Sophie Martin",
  "bio": "Experte en climatologie",
  "contact_info": "sophie.martin@example.com"
}
```

**Réponse (201) :**
```json
{
  "id": 1,
  "name": "Dr. Sophie Martin",
  "bio": "Experte en climatologie",
  "contact_info": "sophie.martin@example.com",
  "created_at": "2025-12-11T10:00:00"
}
```

---

### GET /guests
Lister tous les invités.

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "name": "Dr. Sophie Martin",
    "bio": "...",
    "contact_info": "..."
  }
]
```

---

### GET /guests/{guest_id}
Obtenir un invité par ID.

**Réponse (200) :**
```json
{
  "id": 1,
  "name": "Dr. Sophie Martin",
  "bio": "...",
  "segments": [
    {
      "id": 201,
      "title": "Débat sur le climat"
    }
  ]
}
```

---

### PUT /guests/{guest_id}
Mettre à jour un invité.

### DELETE /guests/{guest_id}
Supprimer un invité (soft delete).

---

## 📡 Émissions

**Base URL :** `/emissions`

**Fichier :** `routeur/emission_route.py`

**Authentification :** Requise

### POST /emissions
Créer une nouvelle émission.

**Body :**
```json
{
  "title": "Morning Show - 11 Déc 2025",
  "date": "2025-12-11",
  "show_id": 1
}
```

**Réponse (201) :**
```json
{
  "id": 101,
  "title": "Morning Show - 11 Déc 2025",
  "date": "2025-12-11",
  "show_id": 1,
  "user_id": 5,
  "created_at": "2025-12-11T10:00:00"
}
```

---

### GET /emissions
Lister toutes les émissions.

**Query params :**
- `skip`, `limit`
- `show_id` : Filtrer par show

**Exemple :**
```bash
GET /emissions?show_id=1&limit=10
```

**Réponse (200) :**
```json
[
  {
    "id": 101,
    "title": "Morning Show - 11 Déc 2025",
    "date": "2025-12-11",
    "show": {
      "id": 1,
      "name": "Morning Show"
    }
  }
]
```

---

### GET /emissions/{emission_id}
Obtenir une émission par ID.

**Réponse (200) :**
```json
{
  "id": 101,
  "title": "Morning Show - 11 Déc 2025",
  "date": "2025-12-11",
  "show": {...},
  "segments": [
    {
      "id": 201,
      "title": "Actualités",
      "start_time": "08:00:00",
      "end_time": "08:15:00"
    }
  ]
}
```

---

### PUT /emissions/{emission_id}
Mettre à jour une émission.

### DELETE /emissions/{emission_id}
Supprimer une émission (soft delete).

---

## ⏱️ Segments

**Base URL :** `/segments`

**Fichier :** `routeur/segment_route.py`

**Authentification :** Requise

### POST /segments
Créer un nouveau segment.

**Body :**
```json
{
  "title": "Actualités",
  "description": "Tour d'horizon de l'actualité",
  "start_time": "08:00:00",
  "end_time": "08:15:00",
  "emission_id": 101,
  "guest_ids": [1, 2]
}
```

**Réponse (201) :**
```json
{
  "id": 201,
  "title": "Actualités",
  "description": "...",
  "start_time": "08:00:00",
  "end_time": "08:15:00",
  "emission_id": 101,
  "guests": [
    {
      "id": 1,
      "name": "Dr. Sophie Martin"
    }
  ]
}
```

---

### GET /segments
Lister tous les segments.

**Query params :**
- `emission_id` : Filtrer par émission

---

### GET /segments/{segment_id}
Obtenir un segment par ID.

### PUT /segments/{segment_id}
Mettre à jour un segment.

### DELETE /segments/{segment_id}
Supprimer un segment (soft delete).

---

## 🔑 Rôles

**Base URL :** `/roles`

**Fichier :** `routeur/role_route.py`

**Authentification :** Requise (admin uniquement)

### POST /roles
Créer un nouveau rôle.

**Body :**
```json
{
  "name": "editor",
  "description": "Peut créer et modifier les shows",
  "permissions": [2, 3, 6, 7]
}
```

**Réponse (201) :**
```json
{
  "id": 1,
  "name": "editor",
  "description": "Peut créer et modifier les shows",
  "permissions": [2, 3, 6, 7]
}
```

---

### GET /roles
Lister tous les rôles.

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "name": "admin",
    "description": "Accès complet"
  },
  {
    "id": 2,
    "name": "editor",
    "description": "Peut créer et modifier"
  }
]
```

---

### GET /roles/{role_id}
Obtenir un rôle par ID.

### PUT /roles/{role_id}
Mettre à jour un rôle.

### DELETE /roles/{role_id}
Supprimer un rôle.

---

## 🔐 Permissions

**Base URL :** `/permissions`

**Fichier :** `routeur/permissions_route.py`

**Authentification :** Requise (admin uniquement)

### POST /permissions
Créer une nouvelle permission.

**Body :**
```json
{
  "name": "delete_show",
  "description": "Permet de supprimer des shows"
}
```

---

### GET /permissions
Lister toutes les permissions.

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "name": "create_show",
    "description": "Créer un show"
  },
  {
    "id": 2,
    "name": "update_show",
    "description": "Modifier un show"
  }
]
```

---

### POST /permissions/assign
Assigner une permission à un utilisateur.

**Body :**
```json
{
  "user_id": 5,
  "permission_id": 2,
  "granted": true
}
```

**Réponse (200) :**
```json
{
  "message": "Permission assigned successfully"
}
```

---

## 📊 Tableau de bord

**Base URL :** `/dashboard`

**Fichier :** `routeur/dashbord_route.py`

**Authentification :** Requise

### GET /dashboard/stats
Obtenir les statistiques globales.

**Réponse (200) :**
```json
{
  "total_shows": 15,
  "total_emissions": 342,
  "total_presenters": 8,
  "total_guests": 127,
  "total_users": 12,
  "recent_emissions": [
    {
      "id": 101,
      "title": "Morning Show - 11 Déc",
      "date": "2025-12-11"
    }
  ]
}
```

---

### GET /dashboard/user-stats
Statistiques de l'utilisateur connecté.

**Réponse (200) :**
```json
{
  "shows_created": 5,
  "emissions_created": 45,
  "presenters_created": 3
}
```

---

## 🔔 Notifications

**Base URL :** `/notifications`

**Fichier :** `routeur/notification_route.py`

**Authentification :** Requise

### GET /notifications
Lister les notifications de l'utilisateur.

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "message": "Nouvelle émission ajoutée",
    "read": false,
    "created_at": "2025-12-11T10:00:00"
  }
]
```

---

### PUT /notifications/{notification_id}/read
Marquer une notification comme lue.

**Réponse (200) :**
```json
{
  "message": "Notification marked as read"
}
```

---

## 🔍 Recherche

**Base URL :** `/search`

**Fichier :** `routeur/search_route/`

**Authentification :** Requise

### GET /search/shows
Rechercher des shows.

**Query params :**
- `q` : Terme de recherche

**Exemple :**
```bash
GET /search/shows?q=morning
```

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "name": "Morning Show",
    "description": "..."
  },
  {
    "id": 5,
    "name": "Good Morning Radio",
    "description": "..."
  }
]
```

---

### GET /search/users
Rechercher des utilisateurs.

**Query params :**
- `q` : Email ou nom

---

### GET /search/presenters
Rechercher des présentateurs.

**Query params :**
- `q` : Nom

---

### GET /search/guests
Rechercher des invités.

**Query params :**
- `q` : Nom

---

## 📝 Audit Logs

**Base URL :** `/audit-logs`

**Fichier :** `routeur/audit_log_route.py`

**Authentification :** Requise (admin uniquement)

### GET /audit-logs
Lister les logs d'audit.

**Query params :**
- `skip`, `limit`
- `user_id` : Filtrer par utilisateur
- `entity_type` : Filtrer par type (Show, User, etc.)
- `action` : Filtrer par action (CREATE, UPDATE, DELETE)

**Exemple :**
```bash
GET /audit-logs?entity_type=Show&action=UPDATE&limit=50
```

**Réponse (200) :**
```json
[
  {
    "id": 1,
    "user_id": 5,
    "action": "UPDATE",
    "entity_type": "Show",
    "entity_id": 1,
    "changes": {
      "name": {
        "old": "Morning Show",
        "new": "Good Morning Show"
      }
    },
    "timestamp": "2025-12-11T10:30:00"
  }
]
```

---

### GET /audit-logs/{log_id}
Obtenir un log spécifique.

**Réponse (200) :**
```json
{
  "id": 1,
  "user_id": 5,
  "user_email": "admin@example.com",
  "action": "UPDATE",
  "entity_type": "Show",
  "entity_id": 1,
  "changes": {...},
  "timestamp": "2025-12-11T10:30:00"
}
```

---

## 📌 Notes importantes

### Rate Limiting
Non implémenté actuellement. À ajouter pour la production.

### Pagination
Tous les endpoints de liste supportent `skip` et `limit` :
```bash
GET /shows?skip=20&limit=10  # Page 3 (10 items par page)
```

### Filtrage
Utilisez les query params pour filtrer :
```bash
GET /emissions?show_id=1&date=2025-12-11
```

### Tri
Non implémenté. À ajouter si nécessaire :
```bash
GET /shows?sort_by=created_at&order=desc
```

---

**Dernière mise à jour :** 11 décembre 2025
