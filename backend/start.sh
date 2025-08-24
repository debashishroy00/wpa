#!/bin/bash
# Memory-optimized startup script for WealthPath AI Backend

# Set Python optimization flags
export PYTHONOPTIMIZE=2
export PYTHONUNBUFFERED=1
export MALLOC_ARENA_MAX=2
export PYTHONDONTWRITEBYTECODE=1

# Log startup info
echo "========================================="
echo "WealthPath AI Backend - Starting"
echo "========================================="
echo "Memory Limit: ${MEMORY_LIMIT:-512MB}"
echo "Port: ${PORT:-8000}"
echo "Python Optimize: $PYTHONOPTIMIZE"
echo "Workers: 1 (memory-optimized)"
echo "========================================="

# Create necessary directories if they don't exist
mkdir -p /tmp/vector_db
mkdir -p /app/logs

# Check if we're in minimal mode (no vector DB)
if [ "$MINIMAL_MODE" = "true" ]; then
    echo "Running in MINIMAL MODE - Vector DB disabled"
    export DISABLE_VECTOR_DB=true
fi

# Start the application with memory-optimized settings
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --limit-max-requests 1000 \
    --limit-concurrency 25 \
    --timeout-keep-alive 5 \
    --log-level ${LOG_LEVEL:-info}