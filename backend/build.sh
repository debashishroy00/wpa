#!/bin/bash
echo "==> Starting WealthPath AI Backend..."
echo "==> Skipping migrations - tables already exist"
exec gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT