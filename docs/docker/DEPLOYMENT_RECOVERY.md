# Guide de Deploiement et Recuperation — Niveau Junior

Ce guide explique comment le serveur demarre, comment les migrations de base de donnees fonctionnent, et comment recuperer en cas de probleme. Tout est ecrit pour etre compris par un developpeur junior.

---

## Table des matieres

1. [Comment le serveur demarre](#1-comment-le-serveur-demarre)
2. [Le script entrypoint.sh](#2-le-script-entrypointsh)
3. [Connexion a la base de donnees](#3-connexion-a-la-base-de-donnees)
4. [Les migrations Alembic](#4-les-migrations-alembic)
5. [Procedure de recuperation complete](#5-procedure-de-recuperation-complete)
6. [Problemes courants et solutions](#6-problemes-courants-et-solutions)
7. [Checklist de deploiement](#7-checklist-de-deploiement)

---

## 1. Comment le serveur demarre

Quand Docker lance le conteneur `audace_api`, voici ce qui se passe dans l'ordre :

```
Docker demarre le conteneur
        |
        v
entrypoint.sh se lance
        |
        v
Etape 1 : Attente de la base de donnees (retry toutes les 2s, max 30 tentatives)
        |
        v
Etape 2 : alembic upgrade head (cree/met a jour les tables)
        |
        v
Etape 3 : gunicorn demarre (API prete a recevoir des requetes)
        |
        v
Healthcheck : GET /version/health toutes les 30s
```

### Pourquoi cet ordre est important

- **Etape 1** : La base de donnees PostgreSQL peut prendre quelques secondes a demarrer. L'API ne doit pas essayer de se connecter avant qu'elle soit prete. Le script fait jusqu'a 30 tentatives espacees de 2 secondes.

- **Etape 2** : Les migrations Alembic creent ou mettent a jour les tables dans la base de donnees. Si c'est un premier deploiement, toutes les tables sont creees depuis zero. Si c'est une mise a jour, seules les nouvelles migrations sont appliquees.

- **Etape 3** : Gunicorn est le serveur web qui execute l'API FastAPI. Il lance 4 workers (processus paralleles) pour gerer les requetes.

---

## 2. Le script entrypoint.sh

Le fichier `entrypoint.sh` est a la racine du projet. C'est le point d'entree du conteneur Docker.

```bash
#!/bin/bash
set -e   # Arrete le script si une commande echoue

# 1. Attente de la DB avec retry intelligent
for i in $(seq 1 30); do
    python -c "from app.db.database import engine; ..."  # Teste la connexion
    if reussi → break
    sinon → sleep 2 et reessayer
done

# 2. Migrations
alembic upgrade head

# 3. Demarrage
exec gunicorn maintest:app ...
```

### Avant (fragile)

L'ancienne methode etait un `sleep 5` suivi de `alembic upgrade head` directement dans le `docker-compose.yml`. Problemes :
- 5 secondes pas toujours suffisantes
- Pas de retry si la DB n'est pas prete
- Si Alembic echoue, le conteneur crashe en boucle sans explication claire

### Apres (robuste)

Le script `entrypoint.sh` :
- Verifie activement que la DB repond (pas juste un delai fixe)
- Retry automatique (30 tentatives x 2s = 1 minute max)
- Message d'erreur clair si la DB n'est pas accessible

---

## 3. Connexion a la base de donnees

### Le probleme des caracteres speciaux

Les mots de passe de base de donnees contiennent souvent des caracteres speciaux (`@`, `*`, `#`, `%`). Ces caracteres posent probleme dans les URLs de connexion.

**Exemple avec un mot de passe `Pass@word*123` :**

```
# MAUVAIS — le @ est interprete comme separateur user:password@host
postgresql://user:Pass@word*123@db:5432/mabase
                     ^
                     Le parser croit que le hostname est "word*123@db"

# BON — URL.create() gere tout automatiquement
URL.create(
    drivername="postgresql",
    username="user",
    password="Pass@word*123",  # Le mot de passe brut, sans encoding
    host="db",
    port=5432,
    database="mabase",
)
```

### La solution : `URL.create()`

Le fichier `app/db/database.py` utilise `sqlalchemy.engine.URL.create()` au lieu de construire manuellement la chaine de connexion. Cette methode :
- Passe le mot de passe **brut** directement au driver PostgreSQL
- Ne met jamais le mot de passe dans une URL textuelle
- Fonctionne avec n'importe quel caractere special

### Pourquoi pas `quote_plus()` ?

L'ancienne methode `urllib.parse.quote_plus()` encodait les caracteres (`@` → `%40`). Mais :
1. Alembic utilise `configparser` en interne, qui interprete `%` comme un token d'interpolation Python (`%(variable)s`)
2. Le `%40` est corrompu par configparser → mot de passe invalide
3. `URL.create()` contourne completement ce probleme

### Alembic et la connexion DB

Le fichier `alembic/env.py` importe l'URL directement depuis `database.py` :

```python
from app.db.database import Base, SQLALCHEMY_DATABASE_URL

# PAS de config.set_main_option() — contourne configparser
connectable = create_engine(SQLALCHEMY_DATABASE_URL, poolclass=pool.NullPool)
```

**Regle :** ne JAMAIS utiliser `config.set_main_option("sqlalchemy.url", ...)` dans `env.py`. Toujours importer l'URL depuis `database.py`.

---

## 4. Les migrations Alembic

### C'est quoi une migration ?

Une migration est un fichier Python qui decrit un changement dans la structure de la base de donnees (ajouter une table, une colonne, etc.). Alembic gere ces migrations comme une chaine : chaque migration connait celle qui la precede.

```
migration_1 (initial) → migration_2 → migration_3 → ... → migration_HEAD
```

### La table `alembic_version`

PostgreSQL contient une table speciale `alembic_version` avec une seule colonne `version_num`. Cette valeur indique quelle est la derniere migration appliquee.

```sql
SELECT * FROM alembic_version;
-- version_num: '014a5b7e642c'  (= la derniere migration appliquee)
```

### Migrations idempotentes

Certaines migrations verifient si une table existe deja avant de la creer :

```python
def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('ma_table'):
        return  # La table existe deja, on ne fait rien
    op.create_table('ma_table', ...)
```

C'est important quand une migration peut etre rejouee (par exemple apres une reinstallation). Sans cette verification, Alembic crashe avec `DuplicateTable`.

### La chaine de migrations actuelle

```
75e8b3bb0750 (initial)
  └── 728d86904477 → e141f13156c7 → ... → a9d4371840fb
        ├── 4d507a930cc2 (social_page_insights — branche A, idempotente)
        └── b7c2e9f4a1d3 (social_page_insights — branche B, idempotente)
              └── cd42bf43298f (MERGE des deux branches)
                    └── ... → 533c75b202df → 014a5b7e642c (HEAD)
```

**Point notable :** il y a une bifurcation (deux branches partant du meme parent) puis un merge. Les deux branches sont idempotentes (`has_table()` check) pour eviter les erreurs `DuplicateTable`.

---

## 5. Procedure de recuperation complete

### Quand utiliser cette procedure ?

- Le serveur est completement plante
- La base de donnees est corrompue
- Reinstallation complete du VPS
- Migration Alembic cassee qui bloque le demarrage

### Etape par etape

```bash
# 1. Se connecter au VPS
ssh dokploy

# 2. Stopper l'API (garder la DB tournante)
sudo docker stop audace_api

# 3. Verifier que la DB tourne
sudo docker ps | grep audace_db
# Si elle est stoppee :
sudo docker start audace_db && sleep 5

# 4. Drop et recreer la base de donnees
sudo docker exec -it audace_db psql -U audace_user -d postgres \
  -c "DROP DATABASE IF EXISTS audace_db;"
sudo docker exec -it audace_db psql -U audace_user -d postgres \
  -c "CREATE DATABASE audace_db OWNER audace_user;"

# 5. Synchroniser le mot de passe PostgreSQL
# Le mot de passe doit correspondre a la variable DATABASE_PASSWORD du conteneur API
# Pour le verifier :
sudo docker exec audace_api printenv DATABASE_PASSWORD
# Puis :
sudo docker exec -it audace_db psql -U audace_user -d audace_db \
  -c "ALTER USER audace_user WITH PASSWORD '<mot_de_passe_vu_ci-dessus>';"

# 6. Redemarrer l'API
sudo docker start audace_api

# 7. Verifier les logs (attendre ~15 secondes)
sleep 15 && sudo docker logs audace_api --tail 50
```

### Ce qui se passe automatiquement

Quand le conteneur redemarre :
1. `entrypoint.sh` attend que la DB soit prete
2. `alembic upgrade head` cree TOUTES les tables depuis zero (DB vide)
3. `create_default_admin()` cree les roles et l'admin par defaut
4. `sync_superadmin_permissions()` active toutes les permissions pour les super_admin
5. L'API demarre normalement

### Verifier que tout fonctionne

```bash
# Status des conteneurs (doit afficher "healthy")
sudo docker ps | grep audace

# Tester le healthcheck
curl -s http://localhost:8000/version/health

# Verifier que les tables existent
sudo docker exec -it audace_db psql -U audace_user -d audace_db \
  -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"

# Verifier la version Alembic
sudo docker exec -it audace_db psql -U audace_user -d audace_db \
  -c "SELECT * FROM alembic_version;"
```

---

## 6. Problemes courants et solutions

### Probleme : "password authentication failed"

**Cause :** le mot de passe dans la variable `DATABASE_PASSWORD` du conteneur API ne correspond pas a celui configure dans PostgreSQL.

**Diagnostic :**
```bash
# Voir le mot de passe vu par l'API
sudo docker exec audace_api printenv DATABASE_PASSWORD
```

**Solution :**
```bash
# Synchroniser le mot de passe PostgreSQL
sudo docker exec -it audace_db psql -U audace_user -d audace_db \
  -c "ALTER USER audace_user WITH PASSWORD '<le_mot_de_passe>';"
sudo docker restart audace_api
```

**Prevention :** utiliser un mot de passe **alphanumerique pur** (pas de `@`, `*`, `#`, `%`) dans la configuration Dokploy.

---

### Probleme : "relation already exists" (DuplicateTable)

**Cause :** Alembic essaie de creer une table qui existe deja. Cela arrive quand `alembic_version` est vide alors que les tables existent dans la DB.

**Solution rapide :**
```bash
# Stamper la version au HEAD sans executer les migrations
sudo docker exec -it audace_db psql -U audace_user -d audace_db -c "
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('014a5b7e642c');
"
sudo docker restart audace_api
```

**Solution propre :** suivre la [procedure de recuperation complete](#5-procedure-de-recuperation-complete) (drop + recreate la DB).

---

### Probleme : "Can't locate revision 'xxx'"

**Cause :** la table `alembic_version` pointe vers une revision qui n'existe plus dans le code.

**Solution :**
```bash
# Trouver le HEAD actuel
sudo docker exec audace_api alembic heads

# Mettre a jour la version
sudo docker exec -it audace_db psql -U audace_user -d audace_db \
  -c "UPDATE alembic_version SET version_num = '<revision_HEAD>';"
sudo docker restart audace_api
```

---

### Probleme : le conteneur DB est aussi stoppe

**Cause :** `docker stop` ou crash du Docker daemon peut stopper tous les conteneurs.

**Solution :**
```bash
# Toujours demarrer la DB en premier
sudo docker start audace_db
sleep 5
# Verifier qu'elle est healthy
sudo docker ps | grep audace_db
# Puis demarrer l'API
sudo docker start audace_api
```

---

### Probleme : "Could not translate host name"

**Cause :** le conteneur API ne peut pas resoudre le nom `db` (le conteneur PostgreSQL). Cela arrive quand les conteneurs ne sont pas sur le meme reseau Docker.

**Solution :**
```bash
# Verifier les reseaux
sudo docker network ls
sudo docker network inspect audace_network

# Redemarrer via docker-compose pour reconfigurer les reseaux
cd <repertoire_du_compose>
sudo docker compose up -d
```

---

## 7. Checklist de deploiement

### Premier deploiement

- [ ] Variable `DATABASE_PASSWORD` configuree dans Dokploy (alphanumerique, pas de `@*#%`)
- [ ] Toutes les variables d'environnement requises sont presentes (voir CLAUDE.md section "Variables d'environnement")
- [ ] Le conteneur PostgreSQL (`audace_db`) est healthy avant de lancer l'API
- [ ] `alembic upgrade head` s'execute sans erreur dans les logs
- [ ] Le healthcheck `/version/health` repond 200
- [ ] Les roles et admin par defaut sont crees (verifier les logs de `init_admin`)

### Mise a jour du code

- [ ] Code pousse sur `main` (Dokploy auto-deploie)
- [ ] Verifier les logs apres redemarrage : `sudo docker logs audace_api --tail 50`
- [ ] Nouvelles migrations appliquees sans erreur
- [ ] Healthcheck toujours OK

### Apres une reinstallation

- [ ] Suivre la [procedure de recuperation complete](#5-procedure-de-recuperation-complete)
- [ ] Verifier que toutes les tables existent
- [ ] Verifier que `alembic_version` est au bon HEAD
- [ ] Reconfigurer les variables d'environnement dans Dokploy
- [ ] Tester un login via l'interface frontend

---

## Schema recapitulatif

```
docker-compose.yml
  ├── audace_db (PostgreSQL 15)
  │     └── Volumes : donnees persistantes
  │
  └── audace_api (FastAPI + Gunicorn)
        ├── Dockerfile
        │     └── ENTRYPOINT → entrypoint.sh
        │
        ├── entrypoint.sh
        │     └── 1. Wait DB → 2. alembic upgrade head → 3. gunicorn
        │
        ├── app/db/database.py
        │     └── URL.create() (gere les chars speciaux du password)
        │
        └── alembic/env.py
              └── Importe SQLALCHEMY_DATABASE_URL depuis database.py
                  (contourne configparser)
```

---

**Derniere mise a jour :** 16 mars 2026
**Auteur :** Documentation automatique (Claude Code)
**Version de l'API :** 1.2.0
