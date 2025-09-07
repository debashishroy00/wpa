# WealthPath AI - Database Migration Guide

This guide helps you migrate user data from your local PostgreSQL database to Supabase production database.

## Prerequisites

1. **Python Dependencies**
   ```bash
   pip install psycopg2-binary
   ```

2. **PostgreSQL Tools** (for backup)
   - Ensure `pg_dump` is available in your PATH
   - Usually installed with PostgreSQL client tools

3. **Environment Variables**
   ```bash
   # Required: Supabase connection string from S1.png
   export SUPABASE_DATABASE_URL="postgresql://postgres.xxx:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
   
   # Optional: Local PostgreSQL settings (defaults shown)
   export LOCAL_PG_HOST="localhost"
   export LOCAL_PG_DATABASE="wealthpath_db"
   export LOCAL_PG_USER="postgres" 
   export LOCAL_PG_PASSWORD="password"
   export LOCAL_PG_PORT="5432"
   ```

## Migration Process

### Step 1: Test Connections
```bash
cd scripts
python migrate_to_supabase.py
# Select option 1 for dry run to test connections
```

### Step 2: Preview Migration (Recommended)
```bash
python migrate_to_supabase.py
# Select option 1 to see what data would be migrated
```

### Step 3: Full Migration with Backup
```bash
python migrate_to_supabase.py
# Select option 2 for full migration
# This will:
# - Create backup of current Supabase data
# - Migrate all tables in correct dependency order
# - Handle conflicts with UPSERT operations
```

## Features

### ✅ Safe Migration
- **Dry run mode** - Preview before migrating
- **Automatic backup** - Creates Supabase backup before migration
- **Conflict handling** - Uses UPSERT to update existing records
- **Dependency order** - Migrates tables in correct foreign key order

### ✅ Comprehensive Logging
- Detailed logs saved to timestamped files
- Console output for real-time monitoring
- Connection testing before migration
- Row count verification

### ✅ Table Coverage
Migrates all WealthPath AI tables:
- `users` - User accounts and authentication
- `user_profiles` - User profile information  
- `user_benefits` - Social security and benefits data
- `user_investment_preferences` - Risk tolerance and preferences
- `user_estate_planning` - Estate planning documents
- `user_insurance_policies` - Insurance coverage data
- `user_goals` - Financial goals and targets
- `user_tax_info` - Tax information and records
- `user_debt_info` - Debt and liability data
- `user_assets` - Asset and investment data
- `conversation_history` - Chat conversation logs
- `simple_vector_store` - Vector embeddings for AI

### ✅ Batch Processing
- Processes data in 100-row batches
- Memory efficient for large datasets
- Progress tracking and error recovery

## Usage Examples

### Migrate Specific Table
```bash
python migrate_to_supabase.py
# Select option 3
# Enter table name: users
# Choose dry run: Y/n
```

### Environment Setup (Windows)
```cmd
set SUPABASE_DATABASE_URL=postgresql://postgres.xxx:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
python migrate_to_supabase.py
```

### Environment Setup (Linux/Mac)
```bash
export SUPABASE_DATABASE_URL="postgresql://postgres.xxx:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
python migrate_to_supabase.py
```

## Migration Strategy

### Data Handling
- **UPSERT Operations**: Existing records are updated, new records are inserted
- **ID Preservation**: All primary keys are maintained
- **Foreign Keys**: Tables migrated in dependency order to avoid FK violations
- **Data Types**: Automatic handling of PostgreSQL-specific types (JSONB, timestamps)

### Conflict Resolution
```sql
INSERT INTO table_name (columns...)
VALUES (values...)
ON CONFLICT (id) DO UPDATE SET
  column1 = EXCLUDED.column1,
  column2 = EXCLUDED.column2
```

### Error Recovery
- Continue migration on non-critical errors
- Detailed error logging for troubleshooting
- Rollback protection via backup

## Troubleshooting

### Connection Issues
```bash
# Test local PostgreSQL
psql -h localhost -U postgres -d wealthpath_db -c "SELECT version();"

# Test Supabase connection  
psql "postgresql://postgres.xxx:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres" -c "SELECT version();"
```

### Common Errors

**Error: `psycopg2` not found**
```bash
pip install psycopg2-binary
```

**Error: `pg_dump` not found**
- Install PostgreSQL client tools
- Add PostgreSQL bin directory to PATH

**Error: Connection refused**
- Check database credentials
- Verify network connectivity
- Confirm database server is running

**Error: Permission denied**
- Verify user has read access to local database
- Verify user has write access to Supabase database
- Check firewall settings

### Migration Logs
All migrations create detailed log files:
```
migration_20240907_143022.log
supabase_backup_20240907_143022.sql
```

## Security Notes

⚠️ **Important Security Considerations**
- Never commit database credentials to git
- Use environment variables for sensitive data
- Verify Supabase connection string is correct
- Test with dry run before production migration
- Keep backup files secure and accessible

## Post-Migration

After successful migration:
1. Verify data integrity in Supabase dashboard
2. Test application functionality with migrated data
3. Update application configuration to use Supabase
4. Archive local database and migration logs
5. Update team on migration completion

## Support

For issues with migration:
1. Check migration logs for specific errors
2. Verify all prerequisites are met
3. Test connections independently
4. Review table schemas match between databases
5. Contact database administrator if needed