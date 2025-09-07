#!/bin/bash
# Environment variables template for database migration
# Copy this file to migrate_env.sh and fill in your actual values
# DO NOT commit migrate_env.sh to git (it's in .gitignore)

# REQUIRED: Supabase connection string from S1.png
export SUPABASE_DATABASE_URL="postgresql://postgres.xxx:[YOUR_PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

# OPTIONAL: Local PostgreSQL settings (adjust if needed)
export LOCAL_PG_HOST="localhost"
export LOCAL_PG_DATABASE="wealthpath_db"
export LOCAL_PG_USER="postgres"
export LOCAL_PG_PASSWORD="password"
export LOCAL_PG_PORT="5432"

# Usage:
# 1. Copy this file: cp migrate_env_template.sh migrate_env.sh
# 2. Edit migrate_env.sh with your actual values
# 3. Source it: source migrate_env.sh
# 4. Run migration: python migrate_to_supabase.py