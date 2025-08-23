-- WealthPath AI - Schema Verification Script
-- Run this after create_all_tables.sql to verify all relationships and constraints

-- =============================================================================
-- VERIFY TABLE CREATION ORDER AND FOREIGN KEYS
-- =============================================================================

DO $$
DECLARE
    missing_tables TEXT[] := ARRAY[]::TEXT[];
    missing_fks TEXT[] := ARRAY[]::TEXT[];
    table_count INTEGER;
    fk_count INTEGER;
    
BEGIN
    RAISE NOTICE '🔍 Verifying WealthPath AI Database Schema...';
    RAISE NOTICE '';
    
    -- =============================================================================
    -- CHECK CORE TABLES EXIST
    -- =============================================================================
    
    RAISE NOTICE '📋 Checking table existence:';
    
    -- Core user tables
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        missing_tables := array_append(missing_tables, 'users');
    ELSE
        RAISE NOTICE '✅ users table exists';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_profiles') THEN
        missing_tables := array_append(missing_tables, 'user_profiles');
    ELSE
        RAISE NOTICE '✅ user_profiles table exists';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_sessions') THEN
        missing_tables := array_append(missing_tables, 'user_sessions');
    ELSE
        RAISE NOTICE '✅ user_sessions table exists';
    END IF;
    
    -- Financial tables
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'financial_accounts') THEN
        missing_tables := array_append(missing_tables, 'financial_accounts');
    ELSE
        RAISE NOTICE '✅ financial_accounts table exists';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'financial_entries') THEN
        missing_tables := array_append(missing_tables, 'financial_entries');
    ELSE
        RAISE NOTICE '✅ financial_entries table exists';
    END IF;
    
    -- Goals tables
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'goals') THEN
        missing_tables := array_append(missing_tables, 'goals');
    ELSE
        RAISE NOTICE '✅ goals table exists';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'financial_goals') THEN
        missing_tables := array_append(missing_tables, 'financial_goals');
    ELSE
        RAISE NOTICE '✅ financial_goals table exists';
    END IF;
    
    -- Get total table count
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name NOT LIKE 'pg_%' 
    AND table_name NOT LIKE 'sql_%'
    AND table_name NOT IN ('schema_migrations', 'ar_internal_metadata');
    
    RAISE NOTICE '';
    RAISE NOTICE '📊 Total tables created: %', table_count;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE WARNING '❌ Missing tables: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE '✅ All expected tables are present';
    END IF;
    
    -- =============================================================================
    -- CHECK FOREIGN KEY RELATIONSHIPS
    -- =============================================================================
    
    RAISE NOTICE '';
    RAISE NOTICE '🔗 Checking foreign key relationships:';
    
    -- User profile -> users
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.referential_constraints 
        WHERE constraint_name LIKE '%user_profiles%user%'
    ) THEN
        missing_fks := array_append(missing_fks, 'user_profiles -> users');
    ELSE
        RAISE NOTICE '✅ user_profiles -> users FK exists';
    END IF;
    
    -- Financial accounts -> users
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.referential_constraints 
        WHERE constraint_name LIKE '%financial_accounts%user%'
    ) THEN
        missing_fks := array_append(missing_fks, 'financial_accounts -> users');
    ELSE
        RAISE NOTICE '✅ financial_accounts -> users FK exists';
    END IF;
    
    -- Financial entries -> users
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.referential_constraints 
        WHERE constraint_name LIKE '%financial_entries%user%'
    ) THEN
        missing_fks := array_append(missing_fks, 'financial_entries -> users');
    ELSE
        RAISE NOTICE '✅ financial_entries -> users FK exists';
    END IF;
    
    -- Goals -> users
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.referential_constraints 
        WHERE constraint_name LIKE '%goals%user%'
    ) THEN
        missing_fks := array_append(missing_fks, 'goals -> users');
    ELSE
        RAISE NOTICE '✅ goals -> users FK exists';
    END IF;
    
    -- Get total FK count
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.referential_constraints
    WHERE constraint_schema = 'public';
    
    RAISE NOTICE '';
    RAISE NOTICE '🔗 Total foreign keys: %', fk_count;
    
    IF array_length(missing_fks, 1) > 0 THEN
        RAISE WARNING '❌ Missing foreign keys: %', array_to_string(missing_fks, ', ');
    ELSE
        RAISE NOTICE '✅ All critical foreign key relationships are present';
    END IF;
    
    -- =============================================================================
    -- CHECK ENUM TYPES
    -- =============================================================================
    
    RAISE NOTICE '';
    RAISE NOTICE '🎭 Checking custom enum types:';
    
    -- Check critical enum types
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_status') THEN
        RAISE NOTICE '✅ user_status enum exists';
    ELSE
        RAISE WARNING '❌ user_status enum missing';
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'account_type') THEN
        RAISE NOTICE '✅ account_type enum exists';
    ELSE
        RAISE WARNING '❌ account_type enum missing';
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'entry_category') THEN
        RAISE NOTICE '✅ entry_category enum exists';
    ELSE
        RAISE WARNING '❌ entry_category enum missing';
    END IF;
    
    -- =============================================================================
    -- CHECK INDEXES
    -- =============================================================================
    
    RAISE NOTICE '';
    RAISE NOTICE '🗂️ Checking key indexes:';
    
    -- Users email index
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_users_email') THEN
        RAISE NOTICE '✅ Users email index exists';
    ELSE
        RAISE WARNING '❌ Users email index missing';
    END IF;
    
    -- Financial entries user_id index
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_financial_entries_user_id') THEN
        RAISE NOTICE '✅ Financial entries user_id index exists';
    ELSE
        RAISE WARNING '❌ Financial entries user_id index missing';
    END IF;
    
    -- Goals user_id index
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_goals_user_id') THEN
        RAISE NOTICE '✅ Goals user_id index exists';
    ELSE
        RAISE WARNING '❌ Goals user_id index missing';
    END IF;
    
    -- =============================================================================
    -- FINAL VERIFICATION SUMMARY
    -- =============================================================================
    
    RAISE NOTICE '';
    RAISE NOTICE '===============================================================================';
    RAISE NOTICE '🎯 SCHEMA VERIFICATION COMPLETE';
    RAISE NOTICE '===============================================================================';
    RAISE NOTICE '';
    
    IF array_length(missing_tables, 1) > 0 OR array_length(missing_fks, 1) > 0 THEN
        RAISE WARNING '❌ Schema verification found issues that need attention';
        RAISE NOTICE '   Please review the warnings above and run create_all_tables.sql again if needed';
    ELSE
        RAISE NOTICE '✅ Schema verification successful!';
        RAISE NOTICE '   All tables, relationships, and key indexes are properly created';
        RAISE NOTICE '';
        RAISE NOTICE '   Next steps:';
        RAISE NOTICE '   1. Run supabase_init.sql for Supabase-specific features';
        RAISE NOTICE '   2. Insert test data if needed';
        RAISE NOTICE '   3. Configure your application connection string';
    END IF;
    
END $$;

-- =============================================================================
-- DETAILED RELATIONSHIP ANALYSIS
-- =============================================================================

-- Show all foreign key relationships
SELECT 
    'Foreign Key Relationships:' as info_type,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- Show table sizes (if populated)
SELECT 
    'Table Information:' as info_type,
    schemaname,
    tablename,
    attname AS column_name,
    typname AS data_type,
    attlen AS max_length
FROM pg_stats 
JOIN pg_attribute ON pg_stats.attname = pg_attribute.attname
JOIN pg_type ON pg_attribute.atttypid = pg_type.oid
WHERE schemaname = 'public'
    AND tablename IN ('users', 'user_profiles', 'financial_accounts', 'financial_entries', 'goals')
ORDER BY tablename, attnum;

-- List all indexes for performance verification
SELECT 
    'Index Information:' as info_type,
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
    AND tablename NOT LIKE 'pg_%'
ORDER BY tablename, indexname;