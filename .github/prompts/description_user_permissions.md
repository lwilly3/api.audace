# Gestion des permissions utilisateur

Ce document décrit comment ajouter et supprimer les permissions suivantes à un utilisateur :
- can_acces_showplan_section
- can_create_showplan
- can_changestatus_owned_showplan
- can_delete_showplan
- can_edit_showplan
- can_archive_showplan
- can_acces_guests_section
- can_view_guests
- can_edit_guests
- can_view_archives

## 1. Backend : mise à jour des permissions

### 1.1 Endpoint HTTP
- Méthode : PUT
- URL : `/permissions/update_permissions/{user_id}`
+<!-- Ancienne version :
- Méthode : PATCH
- URL : `/permissions/users/{user_id}`
-->
- Headers : `Authorization: Bearer <token>`
- Corps de la requête (JSON) :
  ```json
  {
    "permissions": {
      "can_create_showplan": true,
      "can_edit_showplan": false,
      // ...autres permissions à true/false
    }
  }
  ```

### 1.2 Contrôles d’accès
- L’utilisateur connecté doit disposer des droits `can_edit_users` ou `can_manage_roles`.
- Vérification automatique via la dépendance `check_permissions` de `crud_permissions.py`.

### 1.3 Implémentation
- La fonction `update_user_permissions(db, user_id, permissions, current_user_id)` (dans `app/db/crud/crud_permissions.py`) :
  1. Vérifie que l’utilisateur connecté a le droit de modifier (`can_edit_users` ou `can_manage_roles`).
  2. Charge ou crée l’enregistrement `UserPermissions` de l’utilisateur cible.
  3. Parcourt le dictionnaire `permissions` et met à jour les attributs correspondants.
  4. Valide et commit la transaction.
- Exemples d’utilisation :
  ```python
  from fastapi import APIRouter, Depends, HTTPException, status
  from sqlalchemy.orm import Session
  from app.db.database import get_db
  from app.db.crud.crud_permissions import update_user_permissions, check_permissions

  router = APIRouter(prefix="/permissions", tags=["Permissions"])

  @router.put("/update_permissions/{user_id}", dependencies=[Depends(check_permissions)])
  def update_permissions_route(
      user_id: int,
      body: dict,
      db: Session = Depends(get_db),
      current_user=Depends(oauth2.get_current_user)
  ):
      try:
          return update_user_permissions(db, user_id, body.get("permissions", {}), current_user.id)
      except Exception as e:
          raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
  ```

## 2. Frontend : appel de l’API

### 2.1 Requête
- URL : `/permissions/update_permissions/{userId}`
- Méthode : PUT
- Header : Authorization Bearer `<token>`
- Body :
  ```js
  const payload = { permissions: { can_acces_showplan_section: true, can_view_archives: false } };
  axios.put(`/permissions/update_permissions/${userId}`, payload, { headers: { Authorization: `Bearer ${token}` } });
  ```

### 2.2 Gestion de la réponse
- Réponse réussie (200) :
  ```json
  { "message": "Permissions mises à jour avec succès pour l'utilisateur 123", "success": true }
  ```
- Erreurs possibles :
  - 403 Forbidden : droits insuffisants
  - 400 Bad Request : permission invalide ou erreur de validation
  - 500 Internal Server Error : erreur serveur

## 3. Tests unitaires

- Vérifier que seuls les champs listés (permissions autorisées) peuvent être modifiés.
- Cas de succès : un ou plusieurs permissions passent à true/false.
- Cas d’échec : permission non reconnue, utilisateur non autorisé.

## 4. Liste complète des permissions disponibles

- can_acces_showplan_broadcast_section
- can_acces_showplan_section
- can_create_showplan
- can_edit_showplan
- can_archive_showplan
- can_archiveStatusChange_showplan
- can_delete_showplan
- can_destroy_showplan
- can_changestatus_showplan
- can_changestatus_owned_showplan
- can_changestatus_archived_showplan
- can_setOnline_showplan
- can_viewAll_showplan

- can_acces_users_section
- can_view_users
- can_edit_users
- can_desable_users
- can_delete_users

- can_manage_roles
- can_assign_roles

- can_acces_guests_section
- can_view_guests
- can_edit_guests
- can_delete_guests

- can_acces_presenters_section
- can_view_presenters
- can_create_presenters
- can_edit_presenters
- can_delete_presenters

- can_acces_emissions_section
- can_view_emissions
- can_create_emissions
- can_edit_emissions
- can_delete_emissions
- can_manage_emissions

- can_view_notifications
- can_manage_notifications

- can_view_audit_logs
- can_view_login_history

- can_manage_settings

- can_view_messages
- can_send_messages
- can_delete_messages

- can_view_files
- can_upload_files
- can_delete_files

- can_view_tasks
- can_create_tasks
- can_edit_tasks
- can_delete_tasks
- can_assign_tasks

- can_view_archives
- can_destroy_archives
- can_restore_archives
- can_delete_archives

---

*Fin du guide de gestion des permissions utilisateur.*