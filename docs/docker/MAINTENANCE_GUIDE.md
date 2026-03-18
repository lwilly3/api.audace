# 🛠️ Guide de Maintenance - API Audace

Guide complet des commandes pour gérer, surveiller et sauvegarder votre API déployée sur Dokploy.

---

## 📋 Table des matières

1. [Gestion des conteneurs](#gestion-des-conteneurs)
2. [Surveillance et logs](#surveillance-et-logs)
3. [Base de données](#base-de-données)
4. [Sauvegardes](#sauvegardes)
5. [Restauration](#restauration)
6. [Mises à jour](#mises-à-jour)
7. [Dépannage](#dépannage)

---

## 🐳 Gestion des conteneurs

### Voir l'état des conteneurs

```bash
# Voir tous les conteneurs en cours d'exécution
sudo docker ps

# Voir tous les conteneurs (même arrêtés)
sudo docker ps -a

# Voir les statistiques en temps réel (CPU, RAM, réseau)
sudo docker stats
```

### Redémarrer les services

```bash
# Redémarrer l'API
sudo docker restart audace_api

# Redémarrer la base de données
sudo docker restart audace_db

# Redémarrer tous les conteneurs du projet
cd /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code
sudo docker compose restart
```

### Arrêter/Démarrer les services

```bash
# Arrêter l'API
sudo docker stop audace_api

# Démarrer l'API
sudo docker start audace_api

# Arrêter tous les services
sudo docker compose down

# Démarrer tous les services
sudo docker compose up -d
```

---

## 📊 Surveillance et logs

### Consulter les logs

```bash
# Logs de l'API (dernières 100 lignes)
sudo docker logs audace_api --tail 100

# Logs en temps réel (suivre les nouveaux logs)
sudo docker logs -f audace_api

# Logs avec timestamps
sudo docker logs audace_api --timestamps

# Logs de la base de données
sudo docker logs audace_db --tail 50

# Logs depuis une date spécifique
sudo docker logs audace_api --since "2025-12-10T12:00:00"
```

### Vérifier la santé des conteneurs

```bash
# Inspecter l'état de santé de l'API
sudo docker inspect audace_api --format='{{.State.Health.Status}}'

# Détails complets du conteneur
sudo docker inspect audace_api

# Voir les processus dans le conteneur
sudo docker top audace_api
```

### Accéder à un conteneur

```bash
# Ouvrir un shell dans le conteneur API
sudo docker exec -it audace_api /bin/sh

# Exécuter une commande ponctuelle
sudo docker exec audace_api ls -la /app

# Se connecter à PostgreSQL
sudo docker exec -it audace_db psql -U audace_user -d audace_db
```

---

## 💾 Base de données

### Vérifier la connexion PostgreSQL

```bash
# Tester la connexion
sudo docker exec audace_db pg_isready -U audace_user

# Lister les bases de données
sudo docker exec audace_db psql -U audace_user -c "\l"

# Voir les tables de la base
sudo docker exec audace_db psql -U audace_user -d audace_db -c "\dt"

# Compter les enregistrements
sudo docker exec audace_db psql -U audace_user -d audace_db -c "SELECT COUNT(*) FROM users;"
```

### Exécuter des migrations Alembic

```bash
# Voir l'historique des migrations
sudo docker exec audace_api alembic history

# Voir la version actuelle
sudo docker exec audace_api alembic current

# Appliquer toutes les migrations
sudo docker exec audace_api alembic upgrade head

# Revenir à une migration précédente
sudo docker exec audace_api alembic downgrade -1

# Créer une nouvelle migration
sudo docker exec audace_api alembic revision --autogenerate -m "description"
```

---

## 💾 Sauvegardes

### Sauvegarde complète de la base de données

```bash
# Créer le dossier de sauvegarde
mkdir -p ~/backups

# Sauvegarder la base de données (format custom)
sudo docker exec audace_db pg_dump -U audace_user -Fc fastapi > ~/backups/audace_db_$(date +%Y%m%d_%H%M%S).dump

# Sauvegarder en SQL brut
sudo docker exec audace_db pg_dump -U audace_user fastapi > ~/backups/audace_db_$(date +%Y%m%d_%H%M%S).sql

# Sauvegarder avec compression gzip
sudo docker exec audace_db pg_dump -U audace_user fastapi | gzip > ~/backups/audace_db_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Sauvegarde automatique (cron)

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour une sauvegarde quotidienne à 2h du matin
0 2 * * * docker exec audace_db pg_dump -U audace_user fastapi | gzip > /home/ubuntu/backups/audace_db_$(date +\%Y\%m\%d).sql.gz

# Nettoyer les sauvegardes de plus de 30 jours
0 3 * * * find /home/ubuntu/backups -name "audace_db_*.sql.gz" -mtime +30 -delete
```

### Sauvegarde du volume Docker

```bash
# Sauvegarder le volume PostgreSQL
sudo docker run --rm \
  --volumes-from audace_db \
  -v ~/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d_%H%M%S).tar.gz /var/lib/postgresql/data
```

### Exporter les logs de l'application

```bash
# Exporter tous les logs de l'API
sudo docker logs audace_api > ~/backups/api_logs_$(date +%Y%m%d_%H%M%S).log

# Exporter avec compression
sudo docker logs audace_api | gzip > ~/backups/api_logs_$(date +%Y%m%d_%H%M%S).log.gz
```

---

## 🔄 Restauration

### Restaurer la base de données

```bash
# Depuis un dump custom (.dump)
sudo docker exec -i audace_db pg_restore -U audace_user -d audace_db -c < ~/backups/audace_db_20251210.dump

# Depuis un fichier SQL
sudo docker exec -i audace_db psql -U audace_user -d audace_db < ~/backups/audace_db_20251210.sql

# Depuis un fichier compressé
gunzip -c ~/backups/audace_db_20251210.sql.gz | sudo docker exec -i audace_db psql -U audace_user -d audace_db
```

### Restaurer avec suppression/recréation de la base

```bash
# Supprimer et recréer la base
sudo docker exec audace_db psql -U audace_user -c "DROP DATABASE IF EXISTS fastapi;"
sudo docker exec audace_db psql -U audace_user -c "CREATE DATABASE fastapi;"

# Restaurer
sudo docker exec -i audace_db psql -U audace_user -d audace_db < ~/backups/audace_db_20251210.sql
```

### Restaurer le volume Docker

```bash
# Arrêter le conteneur
sudo docker stop audace_db

# Restaurer le volume
sudo docker run --rm \
  --volumes-from audace_db \
  -v ~/backups:/backup \
  alpine sh -c "cd /var/lib/postgresql/data && tar xzf /backup/postgres_volume_20251210.tar.gz --strip 1"

# Redémarrer le conteneur
sudo docker start audace_db
```

---

## 🔄 Mises à jour

### Mettre à jour le code de l'API

```bash
# Méthode 1 : Via Dokploy UI
# → Aller dans l'interface Dokploy
# → Cliquer sur "Redeploy"

# Méthode 2 : Via ligne de commande
cd /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code
sudo git pull origin main
sudo docker compose up -d --build
```

### Mettre à jour les dépendances Python

```bash
# Reconstruire l'image avec les nouvelles dépendances
sudo docker compose build --no-cache api
sudo docker compose up -d api
```

### Mettre à jour PostgreSQL

```bash
# ⚠️ ATTENTION : Toujours sauvegarder avant !
# 1. Sauvegarder
sudo docker exec audace_db pg_dump -U audace_user fastapi > ~/backups/before_upgrade.sql

# 2. Modifier l'image dans docker-compose.yml
# postgres:15-alpine → postgres:16-alpine

# 3. Recréer le conteneur
sudo docker compose up -d db
```

---

## 🔧 Dépannage

### Le conteneur redémarre en boucle

```bash
# Voir les dernières erreurs
sudo docker logs audace_api --tail 50

# Vérifier l'exit code
sudo docker inspect audace_api --format='{{.State.ExitCode}}'

# Désactiver le restart automatique temporairement
sudo docker update --restart=no audace_api
```

### Problème de connexion à la base de données

```bash
# Vérifier que PostgreSQL répond
sudo docker exec audace_db pg_isready

# Tester la connexion depuis l'API
sudo docker exec audace_api psql -h db -U audace_user -d audace_db -c "SELECT 1;"

# Vérifier les variables d'environnement
sudo docker exec audace_api env | grep DATABASE
```

### Espace disque insuffisant

```bash
# Voir l'utilisation du disque
df -h

# Nettoyer les images inutilisées
sudo docker system prune -a

# Nettoyer les volumes inutilisés
sudo docker volume prune

# Voir la taille des conteneurs
sudo docker ps -s
```

### Réinitialiser complètement le projet

```bash
# ⚠️ ATTENTION : Cela supprime TOUTES les données !

# 1. Sauvegarder la base
sudo docker exec audace_db pg_dump -U audace_user fastapi > ~/backups/before_reset.sql

# 2. Tout supprimer
sudo docker compose down -v

# 3. Redéployer
sudo docker compose up -d --build

# 4. Restaurer si nécessaire
sudo docker exec -i audace_db psql -U audace_user -d audace_db < ~/backups/before_reset.sql
```

---

## 📞 Commandes utiles rapides

```bash
# État général du système
sudo docker ps && df -h

# Logs en direct de l'API
sudo docker logs -f audace_api

# Sauvegarder maintenant
sudo docker exec audace_db pg_dump -U audace_user fastapi | gzip > ~/backups/manual_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Redémarrer proprement
sudo docker compose restart

# Vérifier la santé
curl https://api.cloud.audace.ovh/docs
```

---

## 📚 Ressources

- [Documentation Docker](https://docs.docker.com/)
- [Documentation PostgreSQL](https://www.postgresql.org/docs/)
- [Documentation FastAPI](https://fastapi.tiangolo.com/)
- [Documentation Alembic](https://alembic.sqlalchemy.org/)

---

**Dernière mise à jour :** 10 décembre 2025
