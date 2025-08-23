#!/bin/bash
# Render Build Script for WealthPath AI
# This script runs during the build phase on Render

set -e  # Exit on any error

echo "🏗️  Starting WealthPath AI Build Process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install LLM dependencies if available
if [ -f "requirements-llm.txt" ]; then
    echo "🤖 Installing LLM dependencies..."
    pip install -r requirements-llm.txt
fi

# Run database migrations with error handling
echo "🔄 Attempting database setup..."

# Only run migrations if DATABASE_URL is available
if [ -n "$DATABASE_URL" ]; then
    echo "🗄️  Database URL found, attempting migrations..."
    
    # Try Alembic migration first
    if alembic upgrade head 2>/dev/null; then
        echo "✅ Database migrations completed successfully"
    else
        echo "⚠️  Alembic migrations failed during build"
        echo "🚀 Will attempt manual migration during startup"
        
        # Don't fail the build - handle this in startup script
        echo "📝 Build will continue - migrations will be handled at runtime"
    fi
else
    echo "⚠️  DATABASE_URL not available during build (this is normal for Render)"
    echo "🚀 Database setup will be handled during application startup"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p temp

# Set proper permissions
echo "🔐 Setting file permissions..."
find . -name "*.sh" -exec chmod +x {} \;

echo "✅ Build completed successfully!"
echo "🚀 Application will start with: scripts/startup.sh"