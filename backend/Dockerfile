# WealthPath AI Backend
# Clean deployment with simple JSON vector store

FROM python:3.11-slim

WORKDIR /app

# Optimized environment variables
ENV PYTHONOPTIMIZE=2 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app app/
COPY alembic alembic/
COPY alembic.ini .
COPY start.sh .

# Create necessary directories and make start script executable
RUN mkdir -p logs && chmod 755 logs && chmod +x start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:${PORT:-8000}/health')" || exit 1

# Use the flexible start script for maximum platform compatibility
CMD ["./start.sh"]