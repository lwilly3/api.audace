# 🔧 Spécification API Backend - Module Inventaire

> **Document destiné à l'agent backend**
> 
> ⚠️ **ACTION REQUISE : Ajouter les permissions uniquement**
> 
> Le module Inventaire est géré à 100% par Firebase (Firestore + Storage).
> Le backend n'a qu'une seule tâche : **enrichir le système de permissions existant**.

---

## 📋 Contexte rapide

Le module Inventaire permet de gérer les équipements d'un groupe multi-entreprises (BAJ, Trafric, AMG) qui partagent des ressources.

**Architecture :**
- **Données** : Firebase Firestore (collection `equipment/`, `equipment_movements/`, etc.)
- **Fichiers** : Firebase Storage (`inventory/{id}/photos/`, `documents/`)
- **Exports PDF/Excel** : Frontend (jsPDF, xlsx)
- **Auth/Permissions** : API Backend ← **SEUL POINT DE CONTACT**

---

## ✅ Action requise : Ajouter ces permissions

### Nouvelles permissions à intégrer dans `UserPermissions`

```python
# À ajouter dans le modèle de permissions existant

INVENTORY_PERMISSIONS = {
    # Lecture
    "inventory_view": "Voir l'inventaire",
    "inventory_view_all_companies": "Voir l'inventaire de toutes les entreprises",
    "inventory_view_values": "Voir les valeurs/prix des équipements",
    
    # Création/Modification
    "inventory_create": "Ajouter des équipements",
    "inventory_edit": "Modifier les équipements",
    "inventory_delete": "Supprimer/Archiver des équipements",
    
    # Mouvements
    "inventory_move": "Créer des mouvements (attributions, transferts)",
    "inventory_approve_transfers": "Approuver les transferts inter-sites",
    "inventory_approve_company_loans": "Approuver les prêts inter-entreprises",
    
    # Maintenance
    "inventory_maintenance_create": "Créer des maintenances",
    "inventory_maintenance_manage": "Gérer les maintenances",
    
    # Documents
    "inventory_manage_documents": "Gérer les documents/pièces jointes",
    
    # Configuration
    "inventory_manage_settings": "Configurer les listes (catégories, statuts...)",
    "inventory_manage_locations": "Gérer les sites et locaux",
}
```

### Endpoints concernés (existants)

Les endpoints existants doivent accepter ces nouvelles clés :

```http
GET /api/users/{user_id}/permissions
PUT /api/users/{user_id}/permissions
```

### Exemple de requête/réponse

**Requête PUT :**
```json
{
  "permissions": {
    "inventory_view": true,
    "inventory_create": true,
    "inventory_edit": true,
    "inventory_delete": false,
    "inventory_move": true,
    "inventory_manage_settings": false
  }
}
```

**Réponse :**
```json
{
  "success": true,
  "user_id": "user-123",
  "permissions": {
    "inventory_view": true,
    "inventory_create": true,
    ...
  },
  "updated_at": "2026-02-05T10:30:00Z"
}
```

---

## ❌ Ce que le backend NE fait PAS

| Fonctionnalité | Géré par |
|----------------|----------|
| CRUD équipements | Firebase Firestore |
| Mouvements/Historique | Firebase Firestore |
| Documents/Photos | Firebase Storage |
| Configuration listes | Firebase Firestore |
| Exports PDF/Excel | Frontend (jsPDF, xlsx) |
| Temps réel | Firebase onSnapshot |

---

## 📚 Ressources

- **Types de données complets** : voir `.github/skills/inventory/SKILL.md` (section Types)
- **Permissions existantes** : `src/types/permissions.ts`

---

## ✅ Checklist backend

- [ ] Ajouter les 14 permissions `inventory_*` au modèle
- [ ] S'assurer que `GET /users/{id}/permissions` retourne ces clés
- [ ] S'assurer que `PUT /users/{id}/permissions` accepte ces clés
- [ ] Ajouter les permissions à la catégorie "Inventaire" dans l'UI Settings (si applicable)
