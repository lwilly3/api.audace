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

### Securite — Authentification a deux facteurs (2FA/TOTP)
- Systeme 2FA complet base sur TOTP RFC 6238 (Google Authenticator, Authy)
- Router `two_factor_route.py` : 7 endpoints sous `/auth/2fa/*` (setup, verify-setup, verify, verify-backup, disable, backup-codes/regenerate, admin/reset)
- CRUD `crud_2fa.py` : setup, verification OTP, backup codes, admin reset
- Utilitaire `crypto.py` : chiffrement Fernet (AES) des secrets TOTP, bcrypt pour backup codes
- Token temporaire JWT 5 min avec claim `purpose: 2fa_verify` pour le flow login 2FA
- Modification du login (`auth.py`) : bifurcation si `two_factor_enabled` → retourne `{requires_2fa, temp_token}`
- Fonction `create_2fa_temp_token()` et `get_2fa_temp_user()` dans `oauth2.py`
- Dependencies : pyotp>=2.9.0, qrcode[pil]>=7.4

### Securite — Renouvellement silencieux du token
- Endpoint `POST /auth/refresh` : renouvelle un token valide ou recemment expire (fenetre de grace configurable)
- Fonction `decode_token_allow_expired()` dans `oauth2.py` : decode avec grace, rejette tokens revoques et tokens 2FA
- Setting `REFRESH_GRACE_MINUTES` (defaut: 5 min) dans `config.py`
- L'ancien token est revoque, un nouveau est emis avec permissions fraiches
- Audit log `token_refresh` pour tracabilite

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

### Ajouté — Module Social
- Module Social complet : comptes OAuth Facebook, publications, commentaires, messages, analytics
- Service `social_facebook.py` : Graph API v21.0 (pages, posts, commentaires, réactions, insights, publication)
- Service `social_scheduler.py` : scheduler tâches périodiques (auto-sync, auto-optimize, auto-publish)
- Service `ai_service.py` : génération IA de posts depuis URL via Mistral Small
- Service `firebase_cleanup.py` : nettoyage fichiers Firebase Storage après publication
- 43 endpoints REST sous `/social/*` (comptes, posts, inbox, analytics, scheduler, database, stockage)
- Endpoint `POST /social/generate-from-url` : génération IA de posts depuis URL
- Pagination et filtrage par date sur `GET /social/comments` (limit, offset, date_from, date_to)
- Header `X-Total-Count` sur les réponses paginées commentaires
- Auto-publication des posts planifiés via `_run_auto_publish()` dans le scheduler (toutes les 30s)
- Fonction `get_due_scheduled_posts()` pour récupérer les posts planifiés arrivés à échéance
- Nettoyage Firebase Storage : `list_firebase_files()`, `cleanup_orphan_files()` dans `firebase_cleanup.py`
- Endpoint `POST /social/storage/cleanup-orphans` (dry_run + suppression)
- Purge des données publiées : `purge_published_data()` dans `crud_social.py`
- Endpoint `POST /social/database/purge-and-resync` avec resync auto en background
- Fonction `get_post_media_urls()` dans `social_facebook.py` pour récupérer les URLs CDN Facebook
- Insights page-level quotidiens : `get_page_level_insights()` et `_sync_page_insights()`
- Analytics avancées : répartition réactions, tendance abonnés, performance vidéo
- Modèles SQLAlchemy : SocialAccount, SocialPost, SocialPostResult, SocialComment, SocialConversation, SocialMessage, SocialPageInsight
- 14 permissions `social_*` pour contrôle d'accès granulaire

### Corrigé — Module Social
- Doublon de publication planifiée en multi-worker Gunicorn : transition atomique SQL `UPDATE ... WHERE status IN ('draft','scheduled')` + HTTP 409
- Images cassées après publication : remplacement URLs Firebase par URLs Facebook CDN dans `post.media_urls` avant cleanup
- Timezone planification : les dates sont maintenant stockées en UTC

### Modifié
- Modèle `User` : ajout de 3 colonnes (`two_factor_enabled`, `totp_secret_encrypted`, `backup_codes_hash`)
- Modèle `UserPermissions` : ajout de 2 colonnes (`can_enforce_2fa`, `can_reset_user_2fa`)
- Modèle `UserPermissions` : ajout de 8 colonnes booléennes pour les permissions Citations
- Fonction `update_all_permissions_to_true()` dans `app/db/init_admin.py` : inclut maintenant les permissions Citations
- `README.md` : ajout des liens vers la documentation de traçabilité

### Base de données
- Migration Alembic `9f728a09` : ajout colonnes 2FA (`users.two_factor_enabled`, `users.totp_secret_encrypted`, `users.backup_codes_hash`, `user_permissions.can_enforce_2fa`, `user_permissions.can_reset_user_2fa`)
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
