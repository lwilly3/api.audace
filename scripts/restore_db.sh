#!/bin/bash

###############################################################################
# Script de restauration de la base de données PostgreSQL
# Usage: ./restore_db.sh <chemin_vers_backup.sql.gz>
###############################################################################

set -e

# Configuration
CONTAINER_NAME="audace_db"
DB_USER="postgres"
DB_NAME="fastapi"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Vérifier les arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}[ERREUR] Aucun fichier de sauvegarde spécifié${NC}"
    echo "Usage: $0 <chemin_vers_backup.sql.gz>"
    echo ""
    echo "Sauvegardes disponibles:"
    ls -lh /home/ubuntu/backups/audace_db_*.sql.gz 2>/dev/null || echo "Aucune sauvegarde trouvée"
    exit 1
fi

BACKUP_FILE=$1

# Vérifier que le fichier existe
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}[ERREUR] Le fichier $BACKUP_FILE n'existe pas${NC}"
    exit 1
fi

# Vérifier que le conteneur existe
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}[ERREUR] Le conteneur $CONTAINER_NAME n'est pas en cours d'exécution${NC}"
    exit 1
fi

echo -e "${YELLOW}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  ATTENTION: Cette opération va écraser la base actuelle ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Fichier de sauvegarde: ${GREEN}$BACKUP_FILE${NC}"
echo -e "Base de données cible: ${GREEN}$DB_NAME${NC}"
echo ""
read -p "Voulez-vous continuer? (oui/non): " CONFIRM

if [ "$CONFIRM" != "oui" ]; then
    echo -e "${RED}Restauration annulée${NC}"
    exit 0
fi

# Créer une sauvegarde de sécurité avant restauration
SAFETY_BACKUP="/tmp/audace_db_before_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
echo -e "${YELLOW}[INFO] Création d'une sauvegarde de sécurité...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$SAFETY_BACKUP"
echo -e "${GREEN}[OK] Sauvegarde de sécurité créée: $SAFETY_BACKUP${NC}"

# Restaurer la base
echo -e "${YELLOW}[INFO] Restauration en cours...${NC}"

# Déconnecter tous les utilisateurs
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME';" > /dev/null 2>&1

# Supprimer et recréer la base
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;" > /dev/null 2>&1
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" > /dev/null 2>&1

# Restaurer les données
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1

# Vérifier la restauration
TABLE_COUNT=$(docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

if [ "$TABLE_COUNT" -gt 0 ]; then
    echo -e "${GREEN}[OK] Restauration réussie! ($TABLE_COUNT tables restaurées)${NC}"
    echo -e "${GREEN}[INFO] Sauvegarde de sécurité conservée: $SAFETY_BACKUP${NC}"
else
    echo -e "${RED}[ERREUR] La restauration semble avoir échoué${NC}"
    echo -e "${YELLOW}[INFO] Vous pouvez restaurer la sauvegarde de sécurité avec:${NC}"
    echo -e "       $0 $SAFETY_BACKUP"
    exit 1
fi

echo -e "${GREEN}[$(date)] Restauration terminée avec succès ✓${NC}"
