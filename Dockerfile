# Image de base Python
FROM python:3.11-slim

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Métadonnées de l'image
LABEL maintainer="Audace API Team" \
      version="1.2.0" \
      description="Audace API - Gestion des émissions radio"

# Création du répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires pour PostgreSQL et autres
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le code source
COPY . .

# Création du répertoire pour les logs
RUN mkdir -p /app/logs

# Exposition du port
EXPOSE 8000

# Healthcheck utilisant le nouvel endpoint /version/health
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/version/health || exit 1

# Commande par défaut (sera remplacée par docker-compose)
CMD ["gunicorn", "maintest:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]