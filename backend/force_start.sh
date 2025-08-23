#!/bin/bash
# Force start without any migrations - emergency deployment fix
echo "==> FORCE START: WealthPath AI Backend"
echo "==> FORCE START: NO migrations will run"
echo "==> FORCE START: Direct Gunicorn startup"

# Kill any existing processes
pkill -f gunicorn || true
pkill -f uvicorn || true

# Direct start without any database operations
exec gunicorn app.main:app \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT:-8000} \
  --preload \
  --timeout 120