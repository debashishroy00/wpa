# WealthPath AI - Database Deployment Guide

This directory contains SQL scripts to deploy the complete WealthPath AI database schema to Supabase (or any PostgreSQL database).

## 📋 Files Overview

| File | Purpose | When to Use |
|------|---------|-------------|
| `create_all_tables.sql` | Core database schema with all tables, indexes, and relationships | Initial deployment or schema updates |
| `supabase_init.sql` | Supabase-specific features (RLS, auth, realtime) | After core schema, only for Supabase |
| `supabase_basic.sql` | Basic setup without RLS for testing | Alternative to supabase_init.sql for development |
| `create_concurrent_indexes.sql` | Performance indexes (concurrent creation) | After basic setup, for production optimization |
| `drop_all_tables.sql` | Emergency database reset (⚠️ DESTRUCTIVE) | Database corruption or complete reset needed |
| `verify_schema.sql` | Schema validation and relationship verification | After deployment to confirm everything works |

## 🚀 Deployment Steps

### Step 1: Initial Database Setup

1. **Connect to your Supabase database**:
   ```bash
   # Using psql with your Supabase connection string
   psql "postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres?sslmode=require"
   ```

2. **Run the core schema creation**:
   ```sql
   \i create_all_tables.sql
   ```
   
   This creates:
   - ✅ All 25+ tables with proper relationships
   - ✅ All enum types (user_status, account_type, etc.)
   - ✅ All foreign key constraints
   - ✅ Performance indexes
   - ✅ UUID extension for PostgreSQL

### Step 2: Supabase-Specific Features

3. **Run Supabase initialization**:
   ```sql
   \i supabase_init.sql
   ```
   
   This adds:
   - ✅ Row Level Security (RLS) policies
   - ✅ Auth integration functions  
   - ✅ Realtime subscriptions
   - ✅ Storage bucket policies
   - ✅ Data validation triggers
   - ✅ Audit logging
   - ✅ Basic performance indexes

### Step 2b: Performance Optimization (Optional)

4. **Create concurrent indexes for production** (run each separately):
   ```bash
   # For production systems with existing data
   # Run each CREATE INDEX CONCURRENTLY statement individually
   psql -c "CREATE INDEX CONCURRENTLY idx_financial_entries_user_category_date_concurrent ON financial_entries(user_id, category, entry_date);"
   psql -c "CREATE INDEX CONCURRENTLY idx_goals_user_status_priority_concurrent ON goals(user_id, status, priority);"
   # ... etc
   ```
   
   Or for development/testing:
   ```sql
   \i create_concurrent_indexes.sql
   ```

### Step 3: Verification

4. **Verify the deployment**:
   ```sql
   \i verify_schema.sql
   ```
   
   This checks:
   - ✅ All tables exist and are properly structured
   - ✅ Foreign key relationships are correct
   - ✅ Indexes are created for performance
   - ✅ Enum types are properly defined

## 📊 Database Structure

### Core Tables (25+ tables total)

**User Management:**
- `users` - Authentication and basic profile
- `user_sessions` - JWT token management
- `user_profiles` - Detailed user information
- `family_members` - Family and dependents
- `user_benefits` - Social Security, pensions, etc.
- `user_tax_info` - Tax planning information

**Financial Data:**
- `financial_accounts` - Bank accounts, investments
- `financial_entries` - Transactions and manual entries
- `account_balances` - Balance snapshots over time
- `net_worth_snapshots` - Net worth calculations

**Goals System (Dual Version):**
- `financial_goals` - Legacy goals (V1)
- `goals` - Modern goals with UUID (V2)
- `goal_progress` - Progress tracking
- `user_preferences` - Risk tolerance and preferences

**Analytics & ML:**
- `model_predictions` - AI predictions and results
- `user_interactions` - User behavior tracking
- `model_performance_metrics` - ML model validation

**Projections:**
- `projection_assumptions` - Monte Carlo parameters
- `projection_snapshots` - Financial projections
- `projection_sensitivity` - Sensitivity analysis

## 🔒 Security Features (Supabase)

### Row Level Security (RLS)
All tables have RLS policies ensuring users can only access their own data:

```sql
-- Example policy
CREATE POLICY "Users can view own financial data" ON financial_entries
    FOR ALL USING (user_id = current_user_id());
```

### Admin Access
Admin users can override RLS policies for system management:

```sql
CREATE POLICY "Admin full access" ON financial_entries
    FOR ALL USING (is_admin());
```

## 🗄️ Data Types and Enums

The schema includes comprehensive enum types:

- `user_status`: active, inactive, suspended, deleted
- `account_type`: checking, savings, investment, retirement, etc.
- `entry_category`: assets, liabilities, income, expenses
- `goal_status`: draft, active, achieved, paused, abandoned
- `data_quality`: DQ1-DQ4 (API to manual entry quality scale)

## 📈 Performance Optimizations

### Indexes
Critical indexes for query performance:
- User lookup indexes (email, ID)
- Foreign key indexes on all relationships
- Date-based indexes for time-series queries
- Composite indexes for common query patterns

### Materialized Views
- `user_financial_summary` - Pre-computed user financial overview

## 🚨 Emergency Procedures

### Database Reset (⚠️ DESTRUCTIVE)
If you need to completely reset the database:

1. **Backup your data first!**
2. Edit `drop_all_tables.sql` and uncomment the confirmation line
3. Run the drop script:
   ```sql
   \i drop_all_tables.sql
   ```
4. Re-run the deployment steps above

### Rollback Strategy
- Always backup before schema changes
- Test schema changes in development first
- Use Supabase's point-in-time recovery for data issues

## 🔧 Troubleshooting

### Common Issues

**Permission Errors:**
```sql
-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

**Foreign Key Violations:**
- Check table creation order in `create_all_tables.sql`
- Ensure referenced tables exist before dependent tables

**RLS Policy Issues:**
- Verify `current_user_id()` function works with your JWT
- Check Supabase auth configuration

**Missing UUID Extension:**
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

## 📞 Support

If you encounter issues:

1. Check the verification output for specific errors
2. Review Supabase logs for detailed error messages
3. Ensure your PostgreSQL version supports all features (12+)
4. Verify all required extensions are installed

## 🎯 Success Criteria

After successful deployment, you should see:
- ✅ 25+ tables created successfully
- ✅ All foreign keys established
- ✅ RLS policies active and working
- ✅ Demo user `test@gmail.com` can authenticate
- ✅ All indexes created for performance
- ✅ Verification script passes all checks

Your WealthPath AI database is now ready for production use! 🚀