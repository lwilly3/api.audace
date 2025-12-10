#!/bin/bash

###############################################################################
# Script de nettoyage des conteneurs orphelins et conflits Traefik
# Usage: ./cleanup_docker.sh
###############################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  Nettoyage des conteneurs Docker et conflits Traefik    ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# 1. Afficher les conteneurs actuels
echo -e "${YELLOW}[1/5] Conteneurs actuels du projet audace:${NC}"
docker ps -a | grep -E "audace|audaceapi" || echo "Aucun conteneur trouvé"
echo ""

# 2. Arrêter les conteneurs orphelins
echo -e "${YELLOW}[2/5] Arrêt des conteneurs orphelins...${NC}"
docker stop $(docker ps -a | grep -E "audaceapi.*web" | awk '{print $1}') 2>/dev/null || echo "  Aucun conteneur orphelin à arrêter"

# 3. Supprimer les conteneurs orphelins
echo -e "${YELLOW}[3/5] Suppression des conteneurs orphelins...${NC}"
docker rm $(docker ps -a | grep -E "audaceapi.*web" | awk '{print $1}') 2>/dev/null || echo "  Aucun conteneur orphelin à supprimer"

# 4. Nettoyer avec docker compose
echo -e "${YELLOW}[4/5] Nettoyage via docker compose...${NC}"
if [ -f "docker-compose.yml" ]; then
    docker compose down --remove-orphans
    echo -e "${GREEN}  ✓ Nettoyage compose terminé${NC}"
else
    echo -e "${RED}  ✗ Fichier docker-compose.yml non trouvé${NC}"
fi

# 5. Nettoyer les ressources inutilisées
echo -e "${YELLOW}[5/5] Nettoyage des ressources Docker inutilisées...${NC}"
docker system prune -f

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Nettoyage terminé avec succès!                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo -e "  1. Redéployer: ${GREEN}docker compose up -d${NC}"
echo -e "  2. Vérifier: ${GREEN}docker ps${NC}"
echo -e "  3. Tester: ${GREEN}curl https://api.cloud.audace.ovh/${NC}"
