-- WealthPath AI - Basic Supabase Setup (No RLS)
-- Use this for initial testing if you encounter RLS issues
-- Run AFTER create_all_tables.sql

-- =============================================================================
-- ENABLE UUID EXTENSION (if not already enabled)
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- BASIC SUPABASE PERMISSIONS
-- =============================================================================

-- Grant necessary permissions for edge functions and API
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres, service_role;

-- Grant basic access to authenticated users (no RLS restrictions for testing)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT INSERT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT UPDATE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Allow anon users to register/login
GRANT INSERT ON users TO anon;
GRANT SELECT ON users TO anon;

-- =============================================================================
-- BASIC DATA VALIDATION
-- =============================================================================

-- Function to validate email format
CREATE OR REPLACE FUNCTION validate_email(email_input TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email_input ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- INSERT DEMO USER
-- =============================================================================

-- Insert demo user for testing (password: password123)
-- Hash generated with bcrypt rounds=12
INSERT INTO users (email, password_hash, is_active, status, first_name, last_name, created_at)
VALUES (
    'test@gmail.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdkGMYQ7z8E2u',  -- password123
    true,
    'active',
    'Demo',
    'User',
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Get the inserted user ID for demo data
DO $$
DECLARE
    demo_user_id INTEGER;
    demo_profile_id INTEGER;
BEGIN
    -- Get demo user ID
    SELECT id INTO demo_user_id FROM users WHERE email = 'test@gmail.com';
    
    IF demo_user_id IS NOT NULL THEN
        -- Insert demo user profile
        INSERT INTO user_profiles (
            user_id, age, gender, marital_status, state, country, 
            employment_status, occupation, risk_tolerance, 
            retirement_age, retirement_goal, emergency_fund_months,
            social_security_age, social_security_monthly, risk_tolerance_score,
            created_at
        ) VALUES (
            demo_user_id, 35, 'Other', 'Single', 'California', 'USA',
            'Employed', 'Software Engineer', 'Moderate',
            65, 2000000, 6,
            67, 3500, 7,
            NOW()
        ) ON CONFLICT (user_id) DO NOTHING;
        
        -- Get profile ID for further demo data
        SELECT id INTO demo_profile_id FROM user_profiles WHERE user_id = demo_user_id;
        
        -- Insert demo financial account
        INSERT INTO financial_accounts (
            user_id, account_type, institution_name, account_name,
            account_number_masked, is_active, is_manual, created_at
        ) VALUES (
            demo_user_id, 'checking', 'Demo Bank', 'Primary Checking',
            '****1234', true, true, NOW()
        ) ON CONFLICT DO NOTHING;
        
        -- Insert demo financial entry
        INSERT INTO financial_entries (
            user_id, category, subcategory, description, amount,
            currency, frequency, entry_date, data_quality,
            confidence_score, source, is_active, created_at
        ) VALUES (
            demo_user_id, 'assets', 'cash', 'Checking Account Balance', 25000.00,
            'USD', 'one_time', NOW(), 'DQ3',
            1.00, 'manual', true, NOW()
        );
        
        RAISE NOTICE 'Demo user and basic data created successfully for test@gmail.com';
    END IF;
END $$;

-- =============================================================================
-- ENABLE REALTIME (OPTIONAL)
-- =============================================================================

-- Enable realtime for key tables (optional - comment out if not needed)
-- ALTER publication supabase_realtime ADD TABLE users;
-- ALTER publication supabase_realtime ADD TABLE user_profiles;
-- ALTER publication supabase_realtime ADD TABLE financial_entries;

-- =============================================================================
-- BASIC SETUP COMPLETE
-- =============================================================================

SELECT 'Basic Supabase setup complete! You can now:
1. Test login with test@gmail.com / password123
2. Verify all tables are accessible
3. Add RLS policies later with supabase_init.sql if needed' as setup_status;