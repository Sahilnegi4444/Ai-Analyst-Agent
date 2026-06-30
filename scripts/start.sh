#!/bin/sh
# start.sh - Backend startup orchestrator
set -e

# Run schema migrations and vector registrations if requested
if [ "$INIT_DB" = "true" ]; then
    echo "[INIT] Initializing database schema..."
    python -c "from scripts.ingest_all import ensure_database_exists, init_db; ensure_database_exists(); init_db()"
fi

# Run full database clean and dataset seed if requested
if [ "$AUTO_SEED" = "true" ]; then
    echo "[SEED] Seeding database tables and indexing documents..."
    python scripts/ingest_all.py
fi

# Start FastAPI web server
if [ "$ENVIRONMENT" = "production" ]; then
    echo "[START] Starting production Gunicorn/Uvicorn server..."
    # Launch Gunicorn with Uvicorn workers (4 workers default or configurable, timeout 120s)
    exec gunicorn app.main:app \
        -w "${WEB_CONCURRENCY:-4}" \
        -k uvicorn.workers.UvicornWorker \
        -b 0.0.0.0:8000 \
        --timeout 120 \
        --keep-alive 5 \
        --log-level info
else
    echo "[START] Starting development Uvicorn server..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
