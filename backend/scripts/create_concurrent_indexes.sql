-- WealthPath AI - Concurrent Index Creation
-- Run this AFTER supabase_init.sql for optimal performance
-- These indexes are created concurrently to avoid blocking production traffic

-- =============================================================================
-- CONCURRENT INDEX CREATION
-- =============================================================================

-- NOTE: Run each CREATE INDEX CONCURRENTLY statement separately
-- Cannot be run in a transaction block or batch script

-- Financial entries performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_entries_user_category_date_concurrent
ON financial_entries(user_id, category, entry_date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_entries_active_concurrent 
ON financial_entries(user_id, entry_date) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_entries_amount_range
ON financial_entries(user_id, amount) WHERE amount > 1000;

-- Goals performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_goals_user_status_priority_concurrent 
ON goals(user_id, status, priority);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_goals_active_concurrent 
ON goals(user_id, target_date) WHERE status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_goals_target_date_range
ON goals(user_id, target_date) WHERE target_date > CURRENT_DATE;

-- User interactions performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_interactions_user_type_timestamp_concurrent 
ON user_interactions(user_id, interaction_type, timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_interactions_recent
ON user_interactions(user_id, timestamp) WHERE timestamp > (NOW() - INTERVAL '30 days');

-- Financial accounts performance indexes  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_accounts_active_concurrent 
ON financial_accounts(user_id, account_type) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_financial_accounts_sync_status
ON financial_accounts(user_id, last_sync_at) WHERE is_active = true AND last_sync_at IS NOT NULL;

-- Net worth snapshots performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_net_worth_user_date_concurrent
ON net_worth_snapshots(user_id, snapshot_date DESC);

-- Model predictions performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_model_predictions_user_type_status
ON model_predictions(user_id, model_type, status) WHERE status = 'completed';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check index creation status
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE indexname LIKE '%_concurrent'
ORDER BY tablename, indexname;

-- Check index usage statistics (run after some usage)
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%_concurrent'
ORDER BY idx_tup_read DESC;

SELECT 'Concurrent indexes created successfully! 
Run individual CREATE INDEX CONCURRENTLY statements for production deployments.' as status;