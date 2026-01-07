# Changelog

Historique des modifications du projet pour donner du contexte aux agents IA et aux développeurs.

Tous les changements notables de ce projet sont documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

## 🤖 Instructions pour les agents IA

### Mise à jour du changelog
Après chaque modification significative du code, ajouter une entrée dans la section `[Non publié]` :
- Utiliser le type approprié : Ajouté, Modifié, Corrigé, Sécurité, Base de données, etc.
- Être précis et concis
- Inclure les migrations Alembic dans la section "Base de données"
- Marquer les breaking changes avec ⚠️

### ⚠️ Gestion de la taille du fichier
**Quand ce fichier dépasse 300 lignes**, l'agent doit :

1. **Archiver les anciennes versions** dans `docs/changelog/` :
   ```
   docs/changelog/
   ├── CHANGELOG-2026.md    # Versions de 2026
   ├── CHANGELOG-2025.md    # Versions de 2025
   ├── CHANGELOG-2024.md    # Versions de 2024
   └── ...
   ```

2. **Procédure d'archivage** :
   - Créer `docs/changelog/CHANGELOG-{ANNÉE}.md` si nécessaire
   - Déplacer toutes les versions de l'année concernée
   - Garder uniquement l'année en cours et `[Non publié]` dans le fichier principal
   - Ajouter un lien vers les archives en haut du fichier

3. **Format des archives** :
   ```markdown
   # Changelog {ANNÉE}
   
   Archive des versions publiées en {ANNÉE}.
   
   Retour au [CHANGELOG principal](../../CHANGELOG.md)
   
   ---
   
   [Contenu des versions de l'année]
   ```

### Outils disponibles
```bash
# Assistant interactif pour ajouter une entrée
python scripts/add_changelog_entry.py

# Générer une entrée depuis la dernière migration
python scripts/show_migrations_history.py --changelog
```

---

## 📚 Archives des versions précédentes

- [2025](docs/changelog/CHANGELOG-2025.md) - Versions de 2025

---

## [Non publié]

### Ajouté
- Nouvelles permissions pour le module Citations (intégration Firebase)
  - 8 nouvelles permissions : `quotes_view`, `quotes_create`, `quotes_edit`, `quotes_delete`, `quotes_publish`, `stream_transcription_view`, `stream_transcription_create`, `quotes_capture_live`
  - Matrice de permissions par rôle (Admin, Éditeur, Animateur, Community Manager, Invité)
  - Script d'initialisation `scripts/init_quotes_permissions.py`
  - Module `app/db/init_quotes_permissions.py` pour la gestion des permissions
  - Documentation complète dans `QUOTES_PERMISSIONS.md`
- Création automatique des rôles Éditeur, Animateur, Community Manager et Invité s'ils n'existent pas
- Système de traçabilité complet avec instructions pour agents IA
  - Script `scripts/show_migrations_history.py` pour consulter l'historique des migrations
  - Script `scripts/add_changelog_entry.py` pour assistant interactif d'ajout d'entrées
  - Guide complet dans `docs/TRACEABILITY_GUIDE.md`
  - Aide-mémoire dans `TRACEABILITY_CHEATSHEET.md`
  - Archivage automatique des anciennes versions par année
- Système complet de gestion des versions de l'API
  - Module centralisé `app/__version__.py` avec Semantic Versioning
  - Middleware `APIVersionMiddleware` pour headers automatiques de version
  - Endpoints `/version` pour consultation des informations de version
  - Script `scripts/bump_version.py` pour incrémenter automatiquement les versions
  - Guide complet dans `docs/API_VERSIONING.md`
  - Intégration avec le système de changelog

### Modifié
- Modèle `UserPermissions` : ajout de 8 colonnes booléennes pour les permissions Citations
- Fonction `update_all_permissions_to_true()` dans `app/db/init_admin.py` : inclut maintenant les permissions Citations
- `README.md` : ajout des liens vers la documentation de traçabilité

### Base de données
- Migration Alembic `75574b12` : ajout des colonnes de permissions Citations dans `user_permissions`

### Documentation
- Création de `CHANGELOG.md` avec instructions pour agents IA
- Création de `docs/TRACEABILITY_GUIDE.md` - guide complet de traçabilité
- Création de `TRACEABILITY_CHEATSHEET.md` - aide-mémoire rapide
- Archivage des versions 2025 dans `docs/changelog/CHANGELOG-2025.md`

---

## Format des entrées

### Types de changements
- **Ajouté** : pour les nouvelles fonctionnalités
- **Modifié** : pour les changements dans les fonctionnalités existantes
- **Déprécié** : pour les fonctionnalités qui seront bientôt supprimées
- **Supprimé** : pour les fonctionnalités supprimées
- **Corrigé** : pour les corrections de bugs
- **Sécurité** : en cas de vulnérabilités
- **Base de données** : pour les changements de schéma (migrations)
- **Documentation** : pour les changements de documentation

### Structure d'une entrée de version

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Ajouté
- Nouvelle fonctionnalité A
- Nouvelle fonctionnalité B

### Modifié
- Changement dans la fonctionnalité C
- Amélioration de la fonctionnalité D

### Corrigé
- Correction du bug #123
- Correction du problème avec X

### Base de données
- Migration `revision_id` : description du changement

### Sécurité
- Correction de la vulnérabilité CVE-XXXX-XXXX
```

---

## Notes

- Les migrations Alembic sont référencées par leur ID de révision (8 premiers caractères)
- Les issues GitHub peuvent être référencées par `#numéro`
- Les breaking changes doivent être clairement indiqués avec ⚠️
- Les dépendances importantes doivent être mentionnées dans la section appropriée
