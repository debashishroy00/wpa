-- WealthPath AI - Emergency Database Reset Script
-- ⚠️  WARNING: This script will PERMANENTLY DELETE all data!
-- Only run this script if you need to completely reset the database
-- 
-- Usage:
-- 1. Connect to your Supabase database
-- 2. Run this script to drop all tables and data
-- 3. Run create_all_tables.sql to recreate the schema
-- 4. Run supabase_init.sql to add Supabase-specific features

-- =============================================================================
-- SAFETY CONFIRMATION
-- =============================================================================

-- Uncomment the next line to confirm you want to proceed with the destructive reset
-- SET confirm_destructive_reset = 'YES_I_WANT_TO_DELETE_EVERYTHING';

DO $$
BEGIN
    IF current_setting('confirm_destructive_reset', true) != 'YES_I_WANT_TO_DELETE_EVERYTHING' THEN
        RAISE EXCEPTION 'SAFETY STOP: Database reset not confirmed! To proceed: 1) Uncomment the SET command above 2) Re-run this script. This will permanently delete ALL data in the WealthPath AI database.';
    END IF;
END $$;

-- =============================================================================
-- DROP ALL TRIGGERS AND FUNCTIONS FIRST
-- =============================================================================

-- Drop triggers
DROP TRIGGER IF EXISTS validate_user_data_trigger ON users;
DROP TRIGGER IF EXISTS validate_financial_entry_trigger ON financial_entries;
DROP TRIGGER IF EXISTS audit_user_profiles ON user_profiles;
DROP TRIGGER IF EXISTS audit_financial_entries ON financial_entries;
DROP TRIGGER IF EXISTS audit_goals ON goals;

-- Drop functions
DROP FUNCTION IF EXISTS validate_user_data() CASCADE;
DROP FUNCTION IF EXISTS validate_financial_entry() CASCADE;
DROP FUNCTION IF EXISTS log_user_activity() CASCADE;
DROP FUNCTION IF EXISTS current_user_id() CASCADE;
DROP FUNCTION IF EXISTS is_admin() CASCADE;
DROP FUNCTION IF EXISTS refresh_user_financial_summary() CASCADE;

-- =============================================================================
-- DROP MATERIALIZED VIEWS
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS user_financial_summary;

-- =============================================================================
-- DROP ALL TABLES (In reverse dependency order)
-- =============================================================================

-- Drop projection tables
DROP TABLE IF EXISTS projection_sensitivity CASCADE;
DROP TABLE IF EXISTS projection_snapshots CASCADE;
DROP TABLE IF EXISTS projection_assumptions CASCADE;

-- Drop analytics tables
DROP TABLE IF EXISTS ab_test_experiments CASCADE;
DROP TABLE IF EXISTS feature_importance CASCADE;
DROP TABLE IF EXISTS model_performance_metrics CASCADE;
DROP TABLE IF EXISTS user_interactions CASCADE;
DROP TABLE IF EXISTS model_predictions CASCADE;

-- Drop goals V2 tables
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS goal_progress CASCADE;
DROP TABLE IF EXISTS goal_relationships CASCADE;
DROP TABLE IF EXISTS goals_history CASCADE;
DROP TABLE IF EXISTS goals CASCADE;

-- Drop goals V1 tables (legacy)
DROP TABLE IF EXISTS goal_performance_metrics CASCADE;
DROP TABLE IF EXISTS goal_milestones CASCADE;
DROP TABLE IF EXISTS action_plans CASCADE;
DROP TABLE IF EXISTS goal_scenarios CASCADE;
DROP TABLE IF EXISTS financial_goals CASCADE;

-- Drop financial data tables
DROP TABLE IF EXISTS net_worth_snapshots CASCADE;
DROP TABLE IF EXISTS account_balances CASCADE;
DROP TABLE IF EXISTS financial_entries CASCADE;
DROP TABLE IF EXISTS financial_accounts CASCADE;

-- Drop user profile tables
DROP TABLE IF EXISTS user_tax_info CASCADE;
DROP TABLE IF EXISTS user_benefits CASCADE;
DROP TABLE IF EXISTS family_members CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;

-- Drop user management tables
DROP TABLE IF EXISTS user_activity_logs CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- =============================================================================
-- DROP ALL CUSTOM TYPES (ENUMS)
-- =============================================================================

DROP TYPE IF EXISTS interaction_type CASCADE;
DROP TYPE IF EXISTS prediction_status CASCADE;
DROP TYPE IF EXISTS model_type CASCADE;
DROP TYPE IF EXISTS action_status CASCADE;
DROP TYPE IF EXISTS action_priority CASCADE;
DROP TYPE IF EXISTS goal_status CASCADE;
DROP TYPE IF EXISTS goal_type CASCADE;
DROP TYPE IF EXISTS frequency_type CASCADE;
DROP TYPE IF EXISTS data_quality CASCADE;
DROP TYPE IF EXISTS entry_category CASCADE;
DROP TYPE IF EXISTS account_type CASCADE;
DROP TYPE IF EXISTS user_status CASCADE;

-- =============================================================================
-- CLEAN UP SUPABASE SPECIFIC ITEMS
-- =============================================================================

-- Remove from realtime publication (if exists)
DO $$
BEGIN
    -- Only attempt if publication exists
    IF EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS users;
        ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS user_profiles;
        ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS financial_entries;
        ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS goals;
        ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS goal_progress;
        ALTER PUBLICATION supabase_realtime DROP TABLE IF EXISTS net_worth_snapshots;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        -- Ignore errors if publication doesn't exist or tables weren't in it
        NULL;
END $$;

-- Clean up storage buckets (if they exist)
DELETE FROM storage.objects WHERE bucket_id = 'user-documents';
DELETE FROM storage.buckets WHERE id = 'user-documents';

-- =============================================================================
-- CLEAN UP SCHEDULED JOBS (if pg_cron is available)
-- =============================================================================

DO $$
BEGIN
    -- Only attempt if cron schema exists
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'cron') THEN
        -- Delete scheduled jobs
        DELETE FROM cron.job WHERE jobname IN (
            'refresh-financial-summary',
            'cleanup-old-sessions', 
            'cleanup-old-activity'
        );
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        -- Ignore if cron extension is not available
        NULL;
END $$;

-- =============================================================================
-- VERIFY CLEANUP
-- =============================================================================

-- Check for any remaining WealthPath AI tables
DO $$
DECLARE
    remaining_tables TEXT[];
BEGIN
    SELECT array_agg(table_name) INTO remaining_tables
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN (
        'users', 'user_sessions', 'user_activity_logs', 'user_profiles', 
        'family_members', 'user_benefits', 'user_tax_info',
        'financial_accounts', 'financial_entries', 'account_balances', 'net_worth_snapshots',
        'financial_goals', 'goal_scenarios', 'action_plans', 'goal_milestones', 'goal_performance_metrics',
        'goals', 'goals_history', 'goal_relationships', 'goal_progress', 'user_preferences',
        'model_predictions', 'user_interactions', 'model_performance_metrics', 'feature_importance', 'ab_test_experiments',
        'projection_assumptions', 'projection_snapshots', 'projection_sensitivity'
    );
    
    IF remaining_tables IS NOT NULL AND array_length(remaining_tables, 1) > 0 THEN
        RAISE WARNING 'The following tables still exist and may need manual cleanup: %', array_to_string(remaining_tables, ', ');
    ELSE
        RAISE NOTICE '✅ All WealthPath AI tables have been successfully removed.';
    END IF;
END $$;

-- Check for any remaining custom types
DO $$
DECLARE
    remaining_types TEXT[];
BEGIN
    SELECT array_agg(typname) INTO remaining_types
    FROM pg_type t
    JOIN pg_namespace n ON t.typnamespace = n.oid
    WHERE n.nspname = 'public'
    AND t.typtype = 'e'  -- enum types
    AND typname IN (
        'user_status', 'account_type', 'entry_category', 'data_quality', 'frequency_type',
        'goal_type', 'goal_status', 'action_priority', 'action_status',
        'model_type', 'prediction_status', 'interaction_type'
    );
    
    IF remaining_types IS NOT NULL AND array_length(remaining_types, 1) > 0 THEN
        RAISE WARNING 'The following custom types still exist and may need manual cleanup: %', array_to_string(remaining_types, ', ');
    ELSE
        RAISE NOTICE '✅ All WealthPath AI custom types have been successfully removed.';
    END IF;
END $$;

-- =============================================================================
-- RESET COMPLETE
-- =============================================================================

RAISE NOTICE 'DATABASE RESET COMPLETE - All WealthPath AI tables, types, functions, and triggers have been removed. Next steps: 1) Run create_all_tables.sql 2) Run supabase_init.sql 3) Restore data if needed. Database is ready for fresh initialization.';

-- Reset the safety flag
RESET confirm_destructive_reset;