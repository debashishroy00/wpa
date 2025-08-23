#!/bin/bash
echo "==> Starting WealthPath AI Backend..."
echo "==> Skipping migrations - tables already exist in Supabase"
echo "==> Starting Gunicorn server..."

# Just start the app without running migrations
gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT