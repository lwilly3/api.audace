# 🔐 Guide de Sécurisation de la Base de Données

## 📊 État actuel de la protection

✅ **Votre base de données est DÉJÀ protégée** grâce au volume Docker `postgres_data`.

### Ce qui est sûr :
- ✅ Redéployer l'API → Données conservées
- ✅ Supprimer le conteneur → Données conservées
- ✅ `docker compose down` → Données conservées
- ✅ `docker compose restart` → Données conservées

### Ce qui supprime les données :
- ⚠️ `docker compose down -v` (flag `-v` supprime les volumes)
- ⚠️ `docker volume rm postgres_data` (suppression manuelle)

---

## 🚀 Nouvelles améliorations ajoutées

### 1. Dossier de sauvegarde monté

Le fichier `docker-compose.yml` a été mis à jour pour inclure un dossier `/backups` accessible depuis l'hôte :

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
  - backups_data:/backups
```

Cela permet de stocker des sauvegardes **en dehors du conteneur**.

### 2. Script de sauvegarde automatique

**Fichier:** `scripts/backup_db.sh`

#### Installation sur le serveur :

```bash
# 1. Se connecter au serveur
ssh ubuntu@votre-serveur

# 2. Créer le dossier de sauvegarde
mkdir -p ~/backups

# 3. Rendre le script exécutable
cd /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code
chmod +x scripts/backup_db.sh

# 4. Tester le script
./scripts/backup_db.sh
```

#### Automatiser avec Cron :

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour une sauvegarde quotidienne à 2h du matin
0 2 * * * /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code/scripts/backup_db.sh >> /var/log/backup_db.log 2>&1

# Ou toutes les 6 heures
0 */6 * * * /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code/scripts/backup_db.sh >> /var/log/backup_db.log 2>&1
```

### 3. Script de restauration

**Fichier:** `scripts/restore_db.sh`

#### Utilisation :

```bash
# Lister les sauvegardes disponibles
ls -lh ~/backups/audace_db_*.sql.gz

# Restaurer une sauvegarde spécifique
./scripts/restore_db.sh ~/backups/audace_db_20251210_140000.sql.gz
```

**Le script :**
- ✅ Crée une sauvegarde de sécurité avant restauration
- ✅ Demande confirmation avant d'écraser les données
- ✅ Déconnecte les utilisateurs actifs
- ✅ Vérifie que la restauration a réussi

---

## 📦 Stratégie de sauvegarde recommandée

### Option 1 : Sauvegardes locales (sur le VPS)

```bash
# Sauvegardes quotidiennes automatiques
0 2 * * * /path/to/scripts/backup_db.sh

# Conservation : 30 jours
```

**Avantages :**
- ✅ Rapide et automatique
- ✅ Gratuit

**Inconvénients :**
- ⚠️ Si le serveur crash, vous perdez tout

### Option 2 : Sauvegardes distantes (recommandé pour la production)

```bash
# Créer un dossier de sauvegarde
mkdir -p ~/backups

# Installer rclone pour synchroniser avec le cloud
curl https://rclone.org/install.sh | sudo bash

# Configurer un stockage cloud (AWS S3, Google Drive, etc.)
rclone config

# Script de sauvegarde avec envoi sur le cloud
#!/bin/bash
./scripts/backup_db.sh
rclone copy ~/backups/ mycloud:audace-backups/ --max-age 1h
```

**Ajoutez ceci au cron :**
```bash
0 2 * * * /path/to/backup_and_upload.sh >> /var/log/backup_cloud.log 2>&1
```

### Option 3 : Snapshot du volume Docker (avancé)

```bash
# Créer un snapshot du volume
docker run --rm \
  -v postgres_data:/data \
  -v ~/backups:/backup \
  alpine tar czf /backup/postgres_volume_$(date +%Y%m%d_%H%M%S).tar.gz /data

# Restaurer depuis un snapshot
docker run --rm \
  -v postgres_data:/data \
  -v ~/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/postgres_volume_20251210.tar.gz --strip 1"
```

---

## 🛡️ Protection contre les erreurs humaines

### Alias de sécurité (ajoutez dans `~/.bashrc`)

```bash
# Empêcher la suppression accidentelle des volumes
alias docker-compose-down='echo "⚠️  Utilisez docker-compose-down-safe ou docker-compose-down-force"'
alias docker-compose-down-safe='docker compose down'
alias docker-compose-down-force='echo "⚠️  Cela va supprimer les volumes ! Tapez: docker compose down -v"'

# Sauvegarder avant de redéployer
alias redeploy-safe='./scripts/backup_db.sh && cd /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code && git pull && docker compose up -d --build'
```

---

## 📊 Vérifier l'état des volumes

```bash
# Lister tous les volumes
docker volume ls

# Inspecter le volume postgres_data
docker volume inspect postgres_data

# Voir la taille du volume
docker system df -v | grep postgres_data
```

---

## 🚨 Plan de reprise après sinistre (Disaster Recovery)

### Scénario 1 : Le conteneur ne démarre plus

```bash
# 1. Vérifier que le volume existe toujours
docker volume inspect postgres_data

# 2. Recréer le conteneur
cd /etc/dokploy/compose/audaceapi-audaceapi-yrlul5/code
docker compose up -d db

# 3. Vérifier les données
docker exec audace_db psql -U audace_user -d audace_db -c "SELECT COUNT(*) FROM users;"
```

### Scénario 2 : Le volume est corrompu

```bash
# 1. Restaurer depuis une sauvegarde récente
./scripts/restore_db.sh ~/backups/audace_db_derniere.sql.gz
```

### Scénario 3 : Le serveur complet est perdu

```bash
# 1. Installer Docker et Docker Compose sur le nouveau serveur
# 2. Cloner le repo
git clone https://github.com/lwilly3/api.audace.git

# 3. Déployer
cd api.audace
docker compose up -d

# 4. Restaurer depuis une sauvegarde cloud
rclone copy mycloud:audace-backups/audace_db_latest.sql.gz ~/backups/
./scripts/restore_db.sh ~/backups/audace_db_latest.sql.gz
```

---

## ✅ Checklist de sécurité

- [ ] Volume Docker configuré (✅ déjà fait)
- [ ] Script de sauvegarde installé
- [ ] Cron configuré pour sauvegardes automatiques
- [ ] Sauvegardes testées (restauration fonctionnelle)
- [ ] Sauvegardes distantes configurées (recommandé)
- [ ] Plan de reprise documenté
- [ ] Alertes configurées (optionnel)

---

## 📞 Commandes rapides

```bash
# Sauvegarder maintenant
./scripts/backup_db.sh

# Voir les sauvegardes
ls -lh ~/backups/

# Restaurer
./scripts/restore_db.sh ~/backups/audace_db_YYYYMMDD_HHMMSS.sql.gz

# Vérifier l'intégrité du volume
docker volume inspect postgres_data
```

---

**Dernière mise à jour :** 10 décembre 2025
