#!/bin/bash
echo "==> Starting WealthPath AI Backend..."
echo "==> Tables already exist in Supabase - skipping migrations"
echo "==> Starting Gunicorn server directly..."

# Start the server WITHOUT any migrations
exec gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT