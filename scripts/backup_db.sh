#!/bin/bash

###############################################################################
# Script de sauvegarde automatique de la base de données PostgreSQL
# Usage: ./backup_db.sh
###############################################################################

set -e  # Arrêter en cas d'erreur

# Configuration
CONTAINER_NAME="audace_db"
DB_USER="postgres"
DB_NAME="fastapi"
BACKUP_DIR="/home/ubuntu/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="audace_db_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=30

# Couleurs pour les logs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}[$(date)] Démarrage de la sauvegarde...${NC}"

# Créer le dossier de sauvegarde s'il n'existe pas
mkdir -p "$BACKUP_DIR"

# Vérifier que le conteneur existe et tourne
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}[ERREUR] Le conteneur $CONTAINER_NAME n'est pas en cours d'exécution${NC}"
    exit 1
fi

# Effectuer la sauvegarde
echo -e "${YELLOW}[INFO] Sauvegarde de la base $DB_NAME...${NC}"
docker exec "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

# Vérifier que la sauvegarde a réussi
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    FILE_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}[OK] Sauvegarde créée: $BACKUP_FILE (Taille: $FILE_SIZE)${NC}"
else
    echo -e "${RED}[ERREUR] La sauvegarde a échoué${NC}"
    exit 1
fi

# Nettoyer les anciennes sauvegardes
echo -e "${YELLOW}[INFO] Nettoyage des sauvegardes de plus de $RETENTION_DAYS jours...${NC}"
DELETED_COUNT=$(find "$BACKUP_DIR" -name "audace_db_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
echo -e "${GREEN}[OK] $DELETED_COUNT ancienne(s) sauvegarde(s) supprimée(s)${NC}"

# Lister les sauvegardes disponibles
echo -e "${YELLOW}[INFO] Sauvegardes disponibles:${NC}"
ls -lh "$BACKUP_DIR"/audace_db_*.sql.gz 2>/dev/null | tail -5 || echo "Aucune sauvegarde trouvée"

echo -e "${GREEN}[$(date)] Sauvegarde terminée avec succès ✓${NC}"
