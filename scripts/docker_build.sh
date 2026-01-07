#!/bin/bash

# Script pour builder et tester les images Docker
# Usage: ./scripts/docker_build.sh [dev|prod]

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Détection de la version depuis __version__.py
VERSION=$(python3 -c "import sys; sys.path.insert(0, 'app'); from __version__ import get_version; print(get_version())" 2>/dev/null || echo "1.2.0")

# Mode de build (dev ou prod)
MODE=${1:-dev}

print_header "BUILD DOCKER - AUDACE API"

echo "Version détectée : $VERSION"
echo "Mode : $MODE"
echo ""

# Nom de l'image
if [ "$MODE" = "prod" ]; then
    IMAGE_NAME="audace-api:$VERSION"
    DOCKERFILE="Dockerfile.production"
else
    IMAGE_NAME="audace-api:dev"
    DOCKERFILE="Dockerfile"
fi

print_info "Image à construire : $IMAGE_NAME"
print_info "Dockerfile : $DOCKERFILE"
echo ""

# Vérifier que le Dockerfile existe
if [ ! -f "$DOCKERFILE" ]; then
    print_error "Dockerfile '$DOCKERFILE' non trouvé !"
    exit 1
fi

# Build de l'image
print_header "1. Construction de l'image"
docker build -f "$DOCKERFILE" -t "$IMAGE_NAME" . || {
    print_error "Échec de la construction de l'image"
    exit 1
}
print_success "Image construite avec succès"
echo ""

# Afficher la taille de l'image
print_header "2. Informations sur l'image"
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# Test de l'image (optionnel)
read -p "Voulez-vous tester l'image ? (o/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[OoYy]$ ]]; then
    print_header "3. Test de l'image"
    
    # Vérifier si un conteneur du même nom existe déjà
    if docker ps -a --format '{{.Names}}' | grep -q "^audace-api-test$"; then
        print_info "Suppression du conteneur de test existant..."
        docker rm -f audace-api-test >/dev/null 2>&1
    fi
    
    print_info "Démarrage du conteneur de test..."
    docker run -d \
        --name audace-api-test \
        -p 8001:8000 \
        -e DATABASE_HOSTNAME=localhost \
        -e DATABASE_PORT=5432 \
        -e DATABASE_USERNAME=test \
        -e DATABASE_PASSWORD=test \
        -e DATABASE_NAME=test \
        -e SECRET_KEY=test-secret-key \
        "$IMAGE_NAME" || {
        print_error "Échec du démarrage du conteneur"
        exit 1
    }
    
    print_success "Conteneur démarré"
    print_info "Attente du démarrage de l'API (30 secondes)..."
    sleep 30
    
    # Test du healthcheck
    print_info "Test du endpoint /version/health..."
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/version/health)
    
    if [ "$HEALTH_RESPONSE" = "200" ]; then
        print_success "Healthcheck OK (HTTP 200)"
    else
        print_error "Healthcheck échoué (HTTP $HEALTH_RESPONSE)"
    fi
    
    # Test du endpoint /version
    print_info "Test du endpoint /version..."
    VERSION_RESPONSE=$(curl -s http://localhost:8001/version | python3 -m json.tool 2>/dev/null || echo "{}")
    echo "$VERSION_RESPONSE"
    echo ""
    
    # Afficher les logs du conteneur
    print_info "Logs du conteneur (5 dernières lignes):"
    docker logs audace-api-test 2>&1 | tail -5
    echo ""
    
    # Nettoyage
    read -p "Voulez-vous arrêter et supprimer le conteneur de test ? (o/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        docker rm -f audace-api-test >/dev/null 2>&1
        print_success "Conteneur de test supprimé"
    else
        print_info "Conteneur de test toujours actif : audace-api-test"
        print_info "Pour arrêter : docker stop audace-api-test"
        print_info "Pour supprimer : docker rm audace-api-test"
    fi
fi

echo ""
print_header "BUILD TERMINÉ"

print_success "Image $IMAGE_NAME prête"
echo ""
print_info "Commandes utiles :"
echo "  docker images $IMAGE_NAME"
echo "  docker run -p 8000:8000 $IMAGE_NAME"
echo "  docker-compose up -d"

if [ "$MODE" = "prod" ]; then
    echo ""
    print_info "Pour tagger et pousser vers un registry :"
    echo "  docker tag $IMAGE_NAME votre-registry/audace-api:$VERSION"
    echo "  docker push votre-registry/audace-api:$VERSION"
fi

echo ""
