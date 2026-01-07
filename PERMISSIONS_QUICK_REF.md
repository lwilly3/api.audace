# 🔑 Aide-Mémoire - Gestion des Permissions

## 🚀 Guide Rapide

**Pour ajouter/supprimer des permissions**, suivre **OBLIGATOIREMENT** le guide complet :

📖 **[docs/PERMISSIONS_MANAGEMENT_GUIDE.md](docs/PERMISSIONS_MANAGEMENT_GUIDE.md)**

---

## ✅ Checklist ultra-rapide (ajout)

```bash
# 1. Migration
alembic revision -m "add_new_permissions"
# Éditer le fichier migration

# 2. Modèle
# Éditer: app/models/model_user_permissions.py

# 3. CRUD (3 endroits !)
# Éditer: app/db/crud/crud_permissions.py
#   - get_user_permissions() - ligne ~56
#   - initialize_user_permissions() - ligne ~147
#   - update_user_permissions() - ligne ~430

# 4. Init admin
# Éditer: app/db/init_admin.py

# 5. Migration
alembic upgrade head

# 6. Test
curl http://localhost:8000/users/me/permissions

# 7. Documentation + Git
# Créer: MODULE_PERMISSIONS.md
# Éditer: CHANGELOG.md
git add -A && git commit -m "feat: Add [Module] permissions"
```

---

## ⚠️ Points critiques

### Ne JAMAIS oublier ces 3 endroits du CRUD

```python
# app/db/crud/crud_permissions.py

# 1️⃣ get_user_permissions() - Retourne les permissions
return {
    # ... existing ...
    "nouvelle_permission": permissions.nouvelle_permission,  # ← AJOUTER ICI
}

# 2️⃣ initialize_user_permissions() - Initialise les nouveaux users
new_permissions = UserPermissions(
    # ... existing ...
    nouvelle_permission=False,  # ← AJOUTER ICI
)

# 3️⃣ update_user_permissions() - Valide les permissions
valid_permissions = {
    # ... existing ...
    'nouvelle_permission',  # ← AJOUTER ICI
}
```

---

## 🎯 Commandes de validation

```bash
# Vérifier que la permission est partout
grep "nouvelle_permission" app/models/model_user_permissions.py
grep "nouvelle_permission" app/db/crud/crud_permissions.py | wc -l
# Doit retourner 3 (un dans chaque fonction)

# Vérifier les migrations
alembic current
alembic history

# Tester l'API
uvicorn maintest:app --reload
curl http://localhost:8000/users/me/permissions | jq | grep "nouvelle_permission"
```

---

## 📚 Documentation complète

- **Guide complet** : [docs/PERMISSIONS_MANAGEMENT_GUIDE.md](docs/PERMISSIONS_MANAGEMENT_GUIDE.md)
- **Guide Agent IA** : [AGENT.md](AGENT.md) - Section "Procédure 3"
- **Index documentation** : [docs/INDEX.md](docs/INDEX.md)
- **Exemple réel** : [QUOTES_PERMISSIONS.md](QUOTES_PERMISSIONS.md)

---

## 🤖 Pour les agents IA

```
Prompt type pour ajouter des permissions :

"Ajoute les permissions suivantes au système :
- permission_1 : Description
- permission_2 : Description

Matrice de rôles :
- Admin: toutes
- Éditeur: permission_1
- Autres: aucune

Suis STRICTEMENT le guide docs/PERMISSIONS_MANAGEMENT_GUIDE.md"
```

---

**Version** : 1.0.0  
**Mise à jour** : 7 janvier 2026
