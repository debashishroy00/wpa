#!/bin/bash

# WealthPath AI Backend - Flexible Startup Script
# Works with Render, Railway, Docker, and local development

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}

echo "🚀 WealthPath AI Backend Starting..."
echo "📊 Optimized 396MB Docker image - Production ready!"
echo "🔌 Port: $PORT"
echo "📁 Vector Store: Simple JSON (no ML dependencies)"

# Try gunicorn first (for Render/Railway), fallback to uvicorn
if command -v gunicorn &> /dev/null; then
    echo "🎯 Starting with gunicorn + uvicorn workers (production mode)..."
    exec gunicorn app.main:app \
        --workers 1 \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:$PORT \
        --timeout 120 \
        --keep-alive 2 \
        --max-requests 1000 \
        --max-requests-jitter 50 \
        --access-logfile - \
        --error-logfile -
else
    echo "⚡ Starting with uvicorn (development mode)..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port $PORT \
        --workers 1
fi