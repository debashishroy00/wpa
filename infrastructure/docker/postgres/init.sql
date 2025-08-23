-- WealthPath AI Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Create additional schemas for organization
CREATE SCHEMA IF NOT EXISTS financial;
CREATE SCHEMA IF NOT EXISTS ai_models;
CREATE SCHEMA IF NOT EXISTS audit;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- Create enum types for common values
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'deleted');
CREATE TYPE account_type AS ENUM ('checking', 'savings', 'investment', 'retirement', 'credit', 'loan', 'mortgage', 'crypto');
CREATE TYPE goal_type AS ENUM ('early_retirement', 'home_purchase', 'education', 'emergency_fund', 'debt_payoff', 'custom');
CREATE TYPE goal_status AS ENUM ('draft', 'active', 'achieved', 'paused', 'abandoned');
CREATE TYPE entry_category AS ENUM ('assets', 'liabilities', 'income', 'expenses');
CREATE TYPE data_quality AS ENUM ('DQ1', 'DQ2', 'DQ3', 'DQ4');
CREATE TYPE frequency_type AS ENUM ('one-time', 'daily', 'weekly', 'monthly', 'quarterly', 'annually');

-- Set timezone
SET timezone = 'UTC';

-- Create indexes function to be called after tables are created
CREATE OR REPLACE FUNCTION create_performance_indexes() RETURNS void AS $$
BEGIN
    -- User lookup indexes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_users_email_active') THEN
        CREATE INDEX idx_users_email_active ON users(email) WHERE is_active = true;
    END IF;
    
    -- Financial data time-series indexes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_financial_entries_user_date') THEN
        CREATE INDEX idx_financial_entries_user_date ON financial_entries(user_id, entry_date DESC);
    END IF;
    
    -- Goal lookup indexes
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_financial_goals_user_status') THEN
        CREATE INDEX idx_financial_goals_user_status ON financial_goals(user_id, status) WHERE status = 'active';
    END IF;
    
    RAISE NOTICE 'Performance indexes created successfully';
END;
$$ LANGUAGE plpgsql;

-- Log initialization
INSERT INTO information_schema.sql_features (feature_id, feature_name, is_supported) 
VALUES ('WPA001', 'WealthPath AI Database Initialized', 'YES')
ON CONFLICT DO NOTHING;

COMMENT ON DATABASE wealthpath_db IS 'WealthPath AI - Intelligent Financial Planning Platform Database';