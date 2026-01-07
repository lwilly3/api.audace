# Guide Docker - Audace API

## 📦 Fichiers Docker

### Dockerfiles disponibles

1. **`Dockerfile`** - Image standard pour développement et production simple
   - Image de base : `python:3.11-slim`
   - Healthcheck sur `/version/health`
   - 4 workers Gunicorn

2. **`Dockerfile.production`** - Image optimisée multi-stage pour production
   - Build multi-stage (réduit la taille)
   - Utilisateur non-root pour la sécurité
   - Pas de compilateurs dans l'image finale
   - Logs configurés pour stdout/stderr

### Fichiers de configuration

- **`.dockerignore`** - Exclusions pour optimiser la taille de l'image
- **`docker-compose.yml`** - Orchestration avec PostgreSQL
- **`requirements.txt`** - Dépendances Python

## 🚀 Utilisation Rapide

### Build manuel

```bash
# Image de développement
docker build -t audace-api:dev .

# Image de production (multi-stage)
docker build -f Dockerfile.production -t audace-api:1.2.0 .
```

### Build avec script automatisé

```bash
# Mode développement
./scripts/docker_build.sh dev

# Mode production
./scripts/docker_build.sh prod
```

Le script :
- ✅ Détecte automatiquement la version depuis `__version__.py`
- ✅ Build l'image
- ✅ Affiche la taille
- ✅ Teste les endpoints (optionnel)
- ✅ Vérifie le healthcheck

### Docker Compose

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f api

# Arrêter
docker-compose down

# Rebuild et redémarrer
docker-compose up -d --build
```

## 🔄 Migrations Alembic

### Méthodes disponibles

#### 1. Automatique (par défaut)

Les migrations s'exécutent **automatiquement** à chaque démarrage de l'API :

```bash
docker-compose up -d
# Les migrations sont appliquées avant le démarrage de Gunicorn
```

Configuration dans `docker-compose.yml` :
```yaml
command: >
  sh -c "
    alembic upgrade head &&
    gunicorn maintest:app ...
  "
```

#### 2. Service dédié

Pour exécuter les migrations manuellement sans redémarrer l'API :

```bash
# Upgrade vers la dernière version
docker-compose run --rm migrate

# Upgrade vers une version spécifique
docker-compose run --rm migrate alembic upgrade <revision>

# Downgrade d'une version
docker-compose run --rm migrate alembic downgrade -1

# Voir la version actuelle
docker-compose run --rm migrate alembic current

# Historique des migrations
docker-compose run --rm migrate alembic history

# Créer une nouvelle migration
docker-compose run --rm migrate alembic revision --autogenerate -m "description"
```

**Note** : Le service `migrate` utilise le profil `tools` et ne démarre pas automatiquement.

#### 3. Sur conteneur actif

Si le conteneur API est déjà en cours d'exécution :

```bash
# Upgrade
docker-compose exec api alembic upgrade head

# Downgrade
docker-compose exec api alembic downgrade -1

# Version actuelle
docker-compose exec api alembic current

# Historique
docker-compose exec api alembic history
```

#### 4. Script dédié (alternative)

Utiliser le script helper :

```bash
# Upgrade
./scripts/docker_migrate.sh upgrade head

# Downgrade
./scripts/docker_migrate.sh downgrade -1

# Version actuelle
./scripts/docker_migrate.sh current

# Historique
./scripts/docker_migrate.sh history
```

### Cas d'usage

| Situation | Méthode recommandée |
|-----------|-------------------|
| Déploiement initial | Automatique (démarrage) |
| Mise à jour production | Automatique (redémarrage) |
| Développement/test | Service dédié `migrate` |
| Debug migration | `docker-compose exec api` |
| Rollback rapide | Service dédié ou script |

### Vérification post-migration

```bash
# Vérifier la version de la DB
docker-compose exec api alembic current

# Vérifier les logs
docker-compose logs api | grep -i alembic

# Tester la connexion DB
docker-compose exec api python -c "from app.db.database import engine; print(engine.connect())"
```

## 🔍 Vérifications

### Healthcheck

L'image inclut un healthcheck automatique :

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/version/health || exit 1
```

Vérifier manuellement :
```bash
# État du healthcheck
docker ps

# Détails du healthcheck
docker inspect --format='{{json .State.Health}}' <container_id>
```

### Tester l'image localement

```bash
# Lancer un conteneur de test
docker run -d \
  --name audace-api-test \
  -p 8001:8000 \
  -e DATABASE_HOSTNAME=localhost \
  -e DATABASE_PORT=5432 \
  -e DATABASE_USERNAME=test \
  -e DATABASE_PASSWORD=test \
  -e DATABASE_NAME=test \
  -e SECRET_KEY=test-secret-key \
  audace-api:dev

# Tester les endpoints
curl http://localhost:8001/version/health
curl http://localhost:8001/version

# Voir les logs
docker logs audace-api-test

# Nettoyer
docker rm -f audace-api-test
```

## 🔧 Configurations

### Variables d'environnement

L'API nécessite ces variables d'environnement :

```bash
# Base de données
DATABASE_HOSTNAME=db
DATABASE_PORT=5432
DATABASE_USERNAME=audace_user
DATABASE_PASSWORD=<secret>
DATABASE_NAME=audace_db

# Sécurité
SECRET_KEY=<secret>

# Optionnelles
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<secret>
ADMIN_EMAIL=admin@audace.local
```

### Ports

- **8000** : Port de l'API (exposé)
- **5432** : Port PostgreSQL (interne)

## 📊 Optimisations

### Taille des images

```bash
# Comparer les tailles
docker images | grep audace-api

# Image standard (~400MB)
audace-api:dev

# Image production multi-stage (~350MB)
audace-api:1.2.0
```

### Cache des layers

Pour accélérer les builds :

```bash
# Builder avec cache
docker build --cache-from audace-api:latest -t audace-api:new .
```

### Fichiers exclus (.dockerignore)

```
# Documentation
docs/
*.md
CHANGELOG.md

# Développement
test/
scripts/test_*.py

# Logs et backups
backups/
*.log
```

## 🔒 Sécurité

### Image de production

`Dockerfile.production` inclut :
- ✅ Utilisateur non-root (`audace:1000`)
- ✅ Pas de compilateurs dans l'image finale
- ✅ Dépendances minimales
- ✅ Multi-stage build

### Scan de vulnérabilités

```bash
# Scanner l'image (nécessite Docker Scout ou Trivy)
docker scan audace-api:1.2.0

# Ou avec Trivy
trivy image audace-api:1.2.0
```

## 🚢 Déploiement

### Avec Docker Compose (simple)

```bash
# Production
docker-compose up -d

# Avec rebuild
docker-compose up -d --build
```

### Avec Registry (avancé)

```bash
# 1. Tag l'image
docker tag audace-api:1.2.0 registry.example.com/audace-api:1.2.0

# 2. Push vers le registry
docker push registry.example.com/audace-api:1.2.0

# 3. Pull depuis un autre serveur
docker pull registry.example.com/audace-api:1.2.0

# 4. Lancer
docker run -d \
  --name audace-api \
  -p 8000:8000 \
  --env-file .env \
  registry.example.com/audace-api:1.2.0
```

### Avec Dokploy / Traefik

Configuration déjà présente dans `docker-compose.yml` :

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.audace-api-prod.rule=Host(`api.cloud.audace.ovh`)"
  - "traefik.http.routers.audace-api-prod.tls.certresolver=letsencrypt"
```

## 🔄 Mise à jour

### Process de mise à jour

```bash
# 1. Nouvelle version dans __version__.py
python scripts/bump_version.py minor

# 2. Build la nouvelle image
./scripts/docker_build.sh prod

# 3. Tag avec la version
docker tag audace-api:1.3.0 audace-api:latest

# 4. Redéployer
docker-compose up -d --no-deps --build api

# 5. Vérifier
curl https://api.cloud.audace.ovh/version
```

### Rollback

```bash
# Revenir à une version précédente
docker tag audace-api:1.2.0 audace-api:latest
docker-compose up -d --no-deps api
```

## 🐛 Debugging

### Logs

```bash
# Logs en temps réel
docker-compose logs -f api

# Dernières 100 lignes
docker-compose logs --tail=100 api

# Logs d'un conteneur spécifique
docker logs <container_id>
```

### Entrer dans le conteneur

```bash
# Shell interactif
docker exec -it audace_api /bin/bash

# En tant que root (si nécessaire)
docker exec -it --user root audace_api /bin/bash

# Exécuter une commande
docker exec audace_api python -c "from app.__version__ import get_version; print(get_version())"
```

### Inspecter

```bash
# État du conteneur
docker inspect audace_api

# Processus en cours
docker top audace_api

# Statistiques
docker stats audace_api
```

## 📋 Checklist de Build

Avant chaque build de production :

- [ ] Mettre à jour `app/__version__.py`
- [ ] Mettre à jour `CHANGELOG.md`
- [ ] Tester localement avec `./scripts/docker_build.sh prod`
- [ ] Vérifier le healthcheck
- [ ] Tester les endpoints `/version` et `/version/health`
- [ ] Scanner les vulnérabilités
- [ ] Créer un tag Git : `git tag v1.3.0`
- [ ] Pousser l'image vers le registry
- [ ] Déployer en production
- [ ] Vérifier le déploiement

## 🆘 Problèmes Courants

### L'image est trop volumineuse

**Solution** : Utiliser `Dockerfile.production` (multi-stage)

```bash
docker build -f Dockerfile.production -t audace-api:prod .
```

### Le healthcheck échoue

**Causes possibles** :
- Base de données non disponible
- Variables d'environnement manquantes
- Port 8000 déjà utilisé

**Debug** :
```bash
docker logs <container_id>
docker exec <container_id> curl http://localhost:8000/version/health
```

### Erreurs de permissions

**Solution** : Utiliser l'image de production avec utilisateur non-root

```bash
docker build -f Dockerfile.production -t audace-api:prod .
```

### Le build est lent

**Solutions** :
1. Utiliser le cache :
   ```bash
   docker build --cache-from audace-api:latest -t audace-api:new .
   ```

2. Optimiser `.dockerignore`

3. BuildKit :
   ```bash
   DOCKER_BUILDKIT=1 docker build -t audace-api:dev .
   ```

## 🎯 Commandes Utiles

```bash
# Build
./scripts/docker_build.sh prod

# Run local
docker run -d -p 8000:8000 --env-file .env audace-api:dev

# Logs
docker-compose logs -f api

# Shell
docker exec -it audace_api bash

# Migrations
docker-compose run --rm migrate  # Automatique
docker-compose exec api alembic current  # Sur conteneur actif

# Health
docker inspect --format='{{json .State.Health}}' audace_api

# Clean
docker system prune -a

# Stats
docker stats
```

## 🔧 Workflows Courants

### Démarrage initial

```bash
# 1. Créer le fichier .env
cp .env.example .env

# 2. Éditer les variables
nano .env

# 3. Démarrer les services (migrations automatiques)
docker-compose up -d

# 4. Vérifier les logs
docker-compose logs -f api

# 5. Tester l'API
curl https://api.cloud.audace.ovh/version
```

### Mise à jour du code

```bash
# 1. Pull les changements
git pull

# 2. Rebuild et redémarrer (migrations automatiques)
docker-compose up -d --build

# 3. Vérifier la version de la DB
docker-compose exec api alembic current
```

### Rollback de migration

```bash
# 1. Arrêter l'API
docker-compose stop api

# 2. Downgrade la base de données
docker-compose run --rm migrate alembic downgrade -1

# 3. Redémarrer avec l'ancienne version du code
git checkout v1.1.0
docker-compose up -d --build
```

### Debug de migration

```bash
# 1. Voir la version actuelle
docker-compose exec api alembic current

# 2. Voir l'historique complet
docker-compose exec api alembic history

# 3. Logs de la dernière migration
docker-compose logs api | grep -A 20 "Execution des migrations"

# 4. Tester une migration à sec
docker-compose run --rm migrate alembic upgrade head --sql
```
docker inspect --format='{{json .State.Health}}' audace_api

# Clean
docker system prune -a

# Stats
docker stats
```

## 📚 Ressources

- [Dockerfile](Dockerfile) - Image standard
- [Dockerfile.production](Dockerfile.production) - Image optimisée
- [docker-compose.yml](docker-compose.yml) - Orchestration
- [.dockerignore](.dockerignore) - Exclusions
- [Script de build](scripts/docker_build.sh) - Automatisation
