# Image de base Python
FROM python:3.11-slim

# Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

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

# Commande par défaut (sera remplacée par docker-compose)
CMD ["gunicorn", "maintest:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]