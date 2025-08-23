#!/bin/bash
# WealthPath AI - Production Startup Script
# Handles database initialization and migration gracefully

set -e  # Exit on any error

echo "🚀 Starting WealthPath AI Backend..."

# Check if we're in a production environment
if [ "$ENVIRONMENT" = "production" ]; then
    echo "📊 Production environment detected"
else
    echo "🔧 Development environment detected"
fi

# Function to check database connectivity
check_database() {
    echo "🔍 Checking database connectivity..."
    python -c "
import psycopg2
import os
import sys
from urllib.parse import urlparse

try:
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('❌ DATABASE_URL not found')
        sys.exit(1)
    
    # Parse URL and connect
    result = urlparse(db_url)
    conn = psycopg2.connect(
        host=result.hostname,
        port=result.port,
        database=result.path[1:],  # Remove leading slash
        user=result.username,
        password=result.password,
        sslmode='require'
    )
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
"
}

# Function to run migrations safely
run_migrations() {
    echo "🔄 Running database migrations..."
    
    # Try to run Alembic migrations
    if alembic upgrade head 2>/dev/null; then
        echo "✅ Alembic migrations completed successfully"
    else
        echo "⚠️  Alembic migrations failed, trying manual migration..."
        
        # Check if manual migration script exists
        if [ -f "scripts/manual_migration.sql" ]; then
            echo "🛠️  Running manual migration script..."
            python -c "
import psycopg2
import os
from urllib.parse import urlparse

try:
    db_url = os.getenv('DATABASE_URL')
    result = urlparse(db_url)
    conn = psycopg2.connect(
        host=result.hostname,
        port=result.port,
        database=result.path[1:],
        user=result.username,
        password=result.password,
        sslmode='require'
    )
    
    with open('scripts/manual_migration.sql', 'r') as f:
        sql = f.read()
    
    with conn.cursor() as cur:
        cur.execute(sql)
    
    conn.commit()
    conn.close()
    print('✅ Manual migration completed')
except Exception as e:
    print(f'⚠️  Manual migration failed: {e}')
    print('🚀 Continuing with startup (tables may already exist)')
"
        else
            echo "⚠️  Manual migration script not found"
            echo "🚀 Continuing with startup (assuming tables exist)"
        fi
    fi
}

# Function to validate essential tables exist
validate_tables() {
    echo "🔍 Validating essential database tables..."
    python -c "
import psycopg2
import os
import sys
from urllib.parse import urlparse

required_tables = [
    'users', 'user_profiles', 'financial_accounts', 
    'financial_entries', 'goals', 'financial_goals'
]

try:
    db_url = os.getenv('DATABASE_URL')
    result = urlparse(db_url)
    conn = psycopg2.connect(
        host=result.hostname,
        port=result.port,
        database=result.path[1:],
        user=result.username,
        password=result.password,
        sslmode='require'
    )
    
    with conn.cursor() as cur:
        for table in required_tables:
            cur.execute('''
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = %s AND table_schema = 'public'
            ''', (table,))
            
            if cur.fetchone():
                print(f'✅ Table {table} exists')
            else:
                print(f'❌ Table {table} missing')
                
    conn.close()
    print('📊 Table validation completed')
    
except Exception as e:
    print(f'⚠️  Table validation failed: {e}')
    print('🚀 Continuing with startup')
"
}

# Main startup sequence
main() {
    echo "==============================================================================="
    echo "🎯 WealthPath AI Backend Startup"
    echo "==============================================================================="
    
    # Step 1: Check database connectivity
    check_database
    
    # Step 2: Run migrations (with fallback)
    run_migrations
    
    # Step 3: Validate essential tables
    validate_tables
    
    # Step 4: Start the application
    echo "🚀 Starting FastAPI application..."
    echo "==============================================================================="
    
    # Execute the main application
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-1}
}

# Error handling
trap 'echo "❌ Startup failed at line $LINENO"; exit 1' ERR

# Run main function
main "$@"