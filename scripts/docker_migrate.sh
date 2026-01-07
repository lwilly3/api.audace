#!/bin/bash

# Script pour exécuter les migrations Alembic dans Docker
# Usage: ./scripts/docker_migrate.sh [upgrade|downgrade|current|history]

set -e

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Action (par défaut: upgrade head)
ACTION="${1:-upgrade}"
TARGET="${2:-head}"

# Nom du conteneur (essayer plusieurs noms possibles)
CONTAINER_NAME=$(docker ps --format "{{.Names}}" | grep -E "audace.*api|api" | head -n 1)

if [ -z "$CONTAINER_NAME" ]; then
    echo -e "${RED}❌ Aucun conteneur API trouvé${NC}"
    echo "Conteneurs disponibles:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

echo -e "${YELLOW}📦 Conteneur trouvé: ${CONTAINER_NAME}${NC}"

# Construire la commande
case "$ACTION" in
    upgrade)
        CMD="alembic upgrade $TARGET"
        echo -e "${YELLOW}⬆️  Migration vers: $TARGET${NC}"
        ;;
    downgrade)
        CMD="alembic downgrade $TARGET"
        echo -e "${YELLOW}⬇️  Rollback vers: $TARGET${NC}"
        ;;
    current)
        CMD="alembic current"
        echo -e "${YELLOW}📍 Version actuelle de la DB${NC}"
        ;;
    history)
        CMD="alembic history"
        echo -e "${YELLOW}📜 Historique des migrations${NC}"
        ;;
    revision)
        CMD="alembic revision --autogenerate -m '$TARGET'"
        echo -e "${YELLOW}✨ Création d'une nouvelle migration: $TARGET${NC}"
        ;;
    *)
        echo -e "${RED}❌ Action inconnue: $ACTION${NC}"
        echo "Actions disponibles: upgrade, downgrade, current, history, revision"
        exit 1
        ;;
esac

# Exécuter la commande
echo -e "${YELLOW}🚀 Exécution: $CMD${NC}"
echo ""

docker exec "$CONTAINER_NAME" $CMD

echo ""
echo -e "${GREEN}✅ Commande exécutée avec succès${NC}"

# Afficher la version actuelle après upgrade/downgrade
if [[ "$ACTION" == "upgrade" || "$ACTION" == "downgrade" ]]; then
    echo -e "\n${YELLOW}📍 Version actuelle:${NC}"
    docker exec "$CONTAINER_NAME" alembic current
fi
