-- WealthPath AI - Supabase-Specific Initialization
-- Run AFTER create_all_tables.sql to add Supabase-specific features
-- Includes RLS policies, auth integration, and performance optimizations

-- =============================================================================
-- SUPABASE AUTHENTICATION INTEGRATION
-- =============================================================================

-- Enable RLS (Row Level Security) on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_benefits ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tax_info ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE account_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE net_worth_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE goal_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE projection_assumptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE projection_snapshots ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- HELPER FUNCTIONS FOR RLS (Must be created first)
-- =============================================================================

-- Function to get current user ID from JWT
CREATE OR REPLACE FUNCTION current_user_id()
RETURNS INTEGER AS $$
BEGIN
    -- Extract user ID from Supabase JWT claims
    RETURN (current_setting('request.jwt.claims', true)::jsonb ->> 'sub')::integer;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if user has admin role in JWT claims
    RETURN (current_setting('request.jwt.claims', true)::jsonb ->> 'role') = 'admin';
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- ROW LEVEL SECURITY POLICIES
-- =============================================================================

-- Users: Users can only access their own record
CREATE POLICY "Users can view own record" ON users
    FOR SELECT USING (id = current_user_id());

CREATE POLICY "Users can update own record" ON users
    FOR UPDATE USING (id = current_user_id());

-- User Profiles: Users can only access their own profile data
CREATE POLICY "Users can view own profile" ON user_profiles
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own family members" ON family_members
    FOR ALL USING (profile_id IN (
        SELECT id FROM user_profiles WHERE user_id = current_user_id()
    ));

CREATE POLICY "Users can view own benefits" ON user_benefits
    FOR ALL USING (profile_id IN (
        SELECT id FROM user_profiles WHERE user_id = current_user_id()
    ));

CREATE POLICY "Users can view own tax info" ON user_tax_info
    FOR ALL USING (profile_id IN (
        SELECT id FROM user_profiles WHERE user_id = current_user_id()
    ));

-- Financial Data: Users can only access their own financial data
CREATE POLICY "Users can view own financial accounts" ON financial_accounts
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own financial entries" ON financial_entries
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own account balances" ON account_balances
    FOR ALL USING (account_id IN (
        SELECT id FROM financial_accounts WHERE user_id = current_user_id()
    ));

CREATE POLICY "Users can view own net worth" ON net_worth_snapshots
    FOR ALL USING (user_id = current_user_id());

-- Goals V1: Users can only access their own goals
CREATE POLICY "Users can view own financial goals" ON financial_goals
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own goal scenarios" ON goal_scenarios
    FOR ALL USING (goal_id IN (
        SELECT id FROM financial_goals WHERE user_id = current_user_id()
    ));

CREATE POLICY "Users can view own action plans" ON action_plans
    FOR ALL USING (goal_id IN (
        SELECT id FROM financial_goals WHERE user_id = current_user_id()
    ));

CREATE POLICY "Users can view own goal milestones" ON goal_milestones
    FOR ALL USING (goal_id IN (
        SELECT id FROM financial_goals WHERE user_id = current_user_id()
    ));

CREATE POLICY "Users can view own goal performance" ON goal_performance_metrics
    FOR ALL USING (goal_id IN (
        SELECT id FROM financial_goals WHERE user_id = current_user_id()
    ));

-- Goals V2: Users can only access their own goals
CREATE POLICY "Users can view own goals v2" ON goals
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own goal history" ON goals_history
    FOR ALL USING (goal_id IN (
        SELECT goal_id FROM goals WHERE user_id = current_user_id()
    ));

CREATE POLICY "Users can view own goal relationships" ON goal_relationships
    FOR ALL USING (
        parent_goal_id IN (SELECT goal_id FROM goals WHERE user_id = current_user_id()) OR
        child_goal_id IN (SELECT goal_id FROM goals WHERE user_id = current_user_id())
    );

CREATE POLICY "Users can view own goal progress" ON goal_progress
    FOR ALL USING (goal_id IN (
        SELECT goal_id FROM goals WHERE user_id = current_user_id()
    ));

CREATE POLICY "Users can view own preferences" ON user_preferences
    FOR ALL USING (user_id = current_user_id());

-- Analytics: Users can only access their own data
CREATE POLICY "Users can view own model predictions" ON model_predictions
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own interactions" ON user_interactions
    FOR ALL USING (user_id = current_user_id() OR user_id IS NULL);

-- Projections: Users can only access their own projections
CREATE POLICY "Users can view own projection assumptions" ON projection_assumptions
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own projection snapshots" ON projection_snapshots
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own projection sensitivity" ON projection_sensitivity
    FOR ALL USING (snapshot_id IN (
        SELECT id FROM projection_snapshots WHERE user_id = current_user_id()
    ));

-- Sessions and Activity: Users can only access their own sessions and activity
CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR ALL USING (user_id = current_user_id());

CREATE POLICY "Users can view own activity" ON user_activity_logs
    FOR ALL USING (user_id = current_user_id() OR user_id IS NULL);

-- Helper functions already created above

-- =============================================================================
-- ADMIN POLICIES (Override for admin users)
-- =============================================================================

-- Admin users can access all data (add to each table)
CREATE POLICY "Admin full access" ON users
    FOR ALL USING (is_admin());

CREATE POLICY "Admin full access" ON user_profiles
    FOR ALL USING (is_admin());

CREATE POLICY "Admin full access" ON financial_accounts
    FOR ALL USING (is_admin());

CREATE POLICY "Admin full access" ON financial_entries
    FOR ALL USING (is_admin());

CREATE POLICY "Admin full access" ON goals
    FOR ALL USING (is_admin());

CREATE POLICY "Admin full access" ON model_predictions
    FOR ALL USING (is_admin());

-- Add similar admin policies for other tables as needed

-- =============================================================================
-- SUPABASE REALTIME SUBSCRIPTIONS
-- =============================================================================

-- Enable realtime for key tables that need live updates
ALTER publication supabase_realtime ADD TABLE users;
ALTER publication supabase_realtime ADD TABLE user_profiles;
ALTER publication supabase_realtime ADD TABLE financial_entries;
ALTER publication supabase_realtime ADD TABLE goals;
ALTER publication supabase_realtime ADD TABLE goal_progress;
ALTER publication supabase_realtime ADD TABLE net_worth_snapshots;

-- =============================================================================
-- SUPABASE STORAGE BUCKETS (for file uploads)
-- =============================================================================

-- Create storage bucket for user documents
INSERT INTO storage.buckets (id, name, public) VALUES 
('user-documents', 'user-documents', false);

-- Storage policies for user documents
CREATE POLICY "Users can upload own documents" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'user-documents' AND 
        (storage.foldername(name))[1] = current_user_id()::text
    );

CREATE POLICY "Users can view own documents" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'user-documents' AND 
        (storage.foldername(name))[1] = current_user_id()::text
    );

CREATE POLICY "Users can update own documents" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'user-documents' AND 
        (storage.foldername(name))[1] = current_user_id()::text
    );

CREATE POLICY "Users can delete own documents" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'user-documents' AND 
        (storage.foldername(name))[1] = current_user_id()::text
    );

-- =============================================================================
-- PERFORMANCE OPTIMIZATIONS
-- =============================================================================

-- Additional composite indexes for common query patterns
CREATE INDEX idx_financial_entries_user_category_date 
ON financial_entries(user_id, category, entry_date);

CREATE INDEX idx_goals_user_status_priority 
ON goals(user_id, status, priority);

CREATE INDEX idx_user_interactions_user_type_timestamp 
ON user_interactions(user_id, interaction_type, timestamp);

-- Partial indexes for active/common records
CREATE INDEX idx_financial_entries_active 
ON financial_entries(user_id, entry_date) WHERE is_active = true;

CREATE INDEX idx_goals_active 
ON goals(user_id, target_date) WHERE status = 'active';

CREATE INDEX idx_financial_accounts_active 
ON financial_accounts(user_id, account_type) WHERE is_active = true;

-- =============================================================================
-- SUPABASE EDGE FUNCTIONS SETUP
-- =============================================================================

-- Grant necessary permissions for edge functions
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO postgres, service_role;

-- Grant read access to authenticated users (limited by RLS)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT INSERT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT UPDATE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- =============================================================================
-- DATA VALIDATION FUNCTIONS
-- =============================================================================

-- Function to validate user data integrity
CREATE OR REPLACE FUNCTION validate_user_data()
RETURNS TRIGGER AS $$
BEGIN
    -- Validate email format
    IF NEW.email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        RAISE EXCEPTION 'Invalid email format';
    END IF;
    
    -- Ensure phone number is clean (if provided)
    IF NEW.phone_number IS NOT NULL THEN
        NEW.phone_number := regexp_replace(NEW.phone_number, '[^0-9+]', '', 'g');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply validation trigger to users table
CREATE TRIGGER validate_user_data_trigger
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION validate_user_data();

-- Function to validate financial entries
CREATE OR REPLACE FUNCTION validate_financial_entry()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure amount is not zero
    IF NEW.amount = 0 THEN
        RAISE EXCEPTION 'Financial entry amount cannot be zero';
    END IF;
    
    -- Ensure entry_date is not in the far future (more than 1 year)
    IF NEW.entry_date > NOW() + INTERVAL '1 year' THEN
        RAISE EXCEPTION 'Entry date cannot be more than 1 year in the future';
    END IF;
    
    -- Validate allocation percentages sum to 100 (if any are provided)
    IF (COALESCE(NEW.stocks_percentage, 0) + 
        COALESCE(NEW.bonds_percentage, 0) + 
        COALESCE(NEW.real_estate_percentage, 0) + 
        COALESCE(NEW.alternative_percentage, 0)) > 100 THEN
        RAISE EXCEPTION 'Asset allocation percentages cannot exceed 100%%';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply validation trigger to financial entries
CREATE TRIGGER validate_financial_entry_trigger
    BEFORE INSERT OR UPDATE ON financial_entries
    FOR EACH ROW EXECUTE FUNCTION validate_financial_entry();

-- =============================================================================
-- AUDIT TRIGGERS
-- =============================================================================

-- Function to log user activity automatically
CREATE OR REPLACE FUNCTION log_user_activity()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_activity_logs (
        user_id,
        action,
        resource,
        result,
        created_at
    ) VALUES (
        COALESCE(NEW.user_id, OLD.user_id),
        CASE 
            WHEN TG_OP = 'INSERT' THEN 'create'
            WHEN TG_OP = 'UPDATE' THEN 'update'
            WHEN TG_OP = 'DELETE' THEN 'delete'
        END,
        TG_TABLE_NAME,
        'success',
        NOW()
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply audit triggers to key tables
CREATE TRIGGER audit_user_profiles
    AFTER INSERT OR UPDATE OR DELETE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION log_user_activity();

CREATE TRIGGER audit_financial_entries
    AFTER INSERT OR UPDATE OR DELETE ON financial_entries
    FOR EACH ROW EXECUTE FUNCTION log_user_activity();

CREATE TRIGGER audit_goals
    AFTER INSERT OR UPDATE OR DELETE ON goals
    FOR EACH ROW EXECUTE FUNCTION log_user_activity();

-- =============================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE
-- =============================================================================

-- Materialized view for user financial summary
CREATE MATERIALIZED VIEW user_financial_summary AS
SELECT 
    u.id as user_id,
    u.email,
    COALESCE(SUM(CASE WHEN fe.category = 'assets' THEN fe.amount ELSE 0 END), 0) as total_assets,
    COALESCE(SUM(CASE WHEN fe.category = 'liabilities' THEN fe.amount ELSE 0 END), 0) as total_liabilities,
    COALESCE(SUM(CASE WHEN fe.category = 'assets' THEN fe.amount ELSE 0 END), 0) - 
    COALESCE(SUM(CASE WHEN fe.category = 'liabilities' THEN fe.amount ELSE 0 END), 0) as net_worth,
    COUNT(DISTINCT fa.id) as account_count,
    MAX(fe.updated_at) as last_financial_update
FROM users u
LEFT JOIN financial_accounts fa ON u.id = fa.user_id
LEFT JOIN financial_entries fe ON u.id = fe.user_id AND fe.is_active = true
WHERE u.is_active = true
GROUP BY u.id, u.email;

-- Create unique index for materialized view
CREATE UNIQUE INDEX idx_user_financial_summary_user_id ON user_financial_summary(user_id);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_user_financial_summary()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_financial_summary;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- SCHEDULED JOBS (Using pg_cron if available)
-- =============================================================================

-- Note: Requires pg_cron extension to be enabled in Supabase
-- Uncomment if pg_cron is available:

-- SELECT cron.schedule('refresh-financial-summary', '0 2 * * *', 'SELECT refresh_user_financial_summary();');
-- SELECT cron.schedule('cleanup-old-sessions', '0 3 * * *', 'DELETE FROM user_sessions WHERE expires_at < NOW() - INTERVAL ''7 days'';');
-- SELECT cron.schedule('cleanup-old-activity', '0 4 * * 0', 'DELETE FROM user_activity_logs WHERE created_at < NOW() - INTERVAL ''90 days'';');

-- =============================================================================
-- FINAL GRANTS AND PERMISSIONS
-- =============================================================================

-- Ensure anon users can register/login
GRANT INSERT ON users TO anon;
GRANT SELECT ON users TO anon;

-- Ensure service role has full access for backend operations
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- =============================================================================
-- SUPABASE CONFIGURATION COMPLETE
-- =============================================================================

-- Insert initial demo user (if not exists)
INSERT INTO users (email, password_hash, is_active, status, first_name, last_name, created_at)
VALUES (
    'test@gmail.com', 
    '$2b$12$your_hashed_password_here',  -- Replace with actual hashed password
    true,
    'active',
    'Demo',
    'User',
    NOW()
) ON CONFLICT (email) DO NOTHING;

COMMENT ON SCHEMA public IS 'WealthPath AI - Production database schema with Supabase integration, RLS policies, and performance optimizations';

-- Final setup confirmation
DO $$
BEGIN
    RAISE NOTICE 'WealthPath AI Supabase initialization complete!';
    RAISE NOTICE 'Demo user: test@gmail.com (if password hash is updated)';
    RAISE NOTICE 'All RLS policies, triggers, and functions are active.';
END $$;