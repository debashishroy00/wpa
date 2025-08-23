-- WealthPath AI - Manual Migration for Production Deployment
-- Run this if Alembic migrations fail during deployment
-- Safe to run multiple times (uses IF NOT EXISTS)

-- =============================================================================
-- DATA INTEGRITY CONSTRAINTS (from fix_data_integrity_constraints.py)
-- =============================================================================

-- 1. Clean up existing duplicate active accounts first (safe to run multiple times)
WITH duplicates AS (
    SELECT 
        id,
        ROW_NUMBER() OVER (
            PARTITION BY user_id, category, LOWER(TRIM(description)) 
            ORDER BY created_at DESC
        ) as rn
    FROM financial_entries 
    WHERE category = 'assets' 
        AND is_active = true
)
UPDATE financial_entries 
SET is_active = false,
    updated_at = NOW()
WHERE id IN (
    SELECT id FROM duplicates WHERE rn > 1
);

-- 2. Add unique constraint to prevent duplicate active accounts (FIXED - no CONCURRENTLY)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_accounts 
ON financial_entries (user_id, category, LOWER(TRIM(description))) 
WHERE is_active = true AND category = 'assets';

-- 3. Add data quality constraints (safe with IF NOT EXISTS pattern)
DO $$
BEGIN
    -- Ensure asset amounts are not negative (except for specific cases)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_asset_amounts_positive'
    ) THEN
        ALTER TABLE financial_entries 
        ADD CONSTRAINT chk_asset_amounts_positive 
        CHECK (
            category != 'assets' OR 
            amount >= 0 OR 
            description ILIKE '%loss%' OR 
            description ILIKE '%depreciation%'
        );
    END IF;

    -- Ensure reasonable amount limits (catch data entry errors)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_reasonable_amounts'
    ) THEN
        ALTER TABLE financial_entries 
        ADD CONSTRAINT chk_reasonable_amounts 
        CHECK (amount BETWEEN -100000000 AND 100000000);
    END IF;
END $$;

-- 4. Add user profile constraints
DO $$
BEGIN
    -- Ensure reasonable age limits
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_reasonable_age'
    ) THEN
        ALTER TABLE user_profiles 
        ADD CONSTRAINT chk_reasonable_age 
        CHECK (age IS NULL OR (age >= 16 AND age <= 120));
    END IF;
END $$;

-- 5. Add financial goal constraints
DO $$
BEGIN
    -- Ensure goal amounts are positive
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_positive_goal_amounts'
    ) THEN
        ALTER TABLE financial_goals 
        ADD CONSTRAINT chk_positive_goal_amounts 
        CHECK (target_amount > 0);
    END IF;

    -- Ensure target dates are in the future (at time of creation)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.check_constraints 
        WHERE constraint_name = 'chk_future_target_dates'
    ) THEN
        ALTER TABLE financial_goals 
        ADD CONSTRAINT chk_future_target_dates 
        CHECK (target_date > created_at::date);
    END IF;
END $$;

-- 6. Create performance indexes (safe with IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_financial_entries_user_category_active
ON financial_entries (user_id, category, is_active);

CREATE INDEX IF NOT EXISTS idx_financial_entries_subcategory
ON financial_entries (subcategory);

CREATE INDEX IF NOT EXISTS idx_financial_goals_user_type
ON financial_goals (user_id, goal_type);

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify constraints were added
SELECT 
    'Data integrity constraints applied:' as status,
    COUNT(*) as constraint_count
FROM information_schema.check_constraints 
WHERE constraint_name IN (
    'chk_asset_amounts_positive',
    'chk_reasonable_amounts', 
    'chk_reasonable_age',
    'chk_positive_goal_amounts',
    'chk_future_target_dates'
);

-- Verify indexes were created
SELECT 
    'Performance indexes created:' as status,
    COUNT(*) as index_count
FROM pg_indexes 
WHERE indexname IN (
    'idx_unique_active_accounts',
    'idx_financial_entries_user_category_active',
    'idx_financial_entries_subcategory',
    'idx_financial_goals_user_type'
);

SELECT 'Manual migration completed successfully!' as final_status;