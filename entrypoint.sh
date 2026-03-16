#!/bin/bash
set -e

# =============================================================
# Entrypoint robuste pour le conteneur audace_api
# - Attend que PostgreSQL soit pret (avec retry)
# - Execute les migrations Alembic de maniere securisee
# - Demarre gunicorn/uvicorn
# =============================================================

MAX_RETRIES=30
RETRY_INTERVAL=2

echo "Attente de la base de donnees..."
for i in $(seq 1 $MAX_RETRIES); do
    if python -c "
from app.db.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
" 2>/dev/null; then
        echo "Base de donnees prete."
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "ERREUR: impossible de se connecter a la base de donnees apres $MAX_RETRIES tentatives."
        exit 1
    fi
    echo "  tentative $i/$MAX_RETRIES..."
    sleep $RETRY_INTERVAL
done

echo "Execution des migrations Alembic..."
alembic upgrade head

echo "Demarrage de API..."
exec gunicorn maintest:app \
    --workers "${WORKERS:-4}" \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --forwarded-allow-ips='*' \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
