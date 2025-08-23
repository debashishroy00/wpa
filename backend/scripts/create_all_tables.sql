-- WealthPath AI - Complete Database Schema for Supabase
-- Generated from SQLAlchemy models for production deployment
-- Run in order to create all tables with proper dependencies

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- CORE USER MANAGEMENT TABLES
-- =============================================================================

-- User Status Enum
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'deleted');

-- Users table (core authentication)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    status user_status DEFAULT 'active' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NULL,
    last_login_at TIMESTAMPTZ DEFAULT NULL,
    email_verified_at TIMESTAMPTZ DEFAULT NULL,
    first_name VARCHAR(100) DEFAULT NULL,
    last_name VARCHAR(100) DEFAULT NULL,
    phone_number VARCHAR(20) DEFAULT NULL
);

-- User sessions for JWT token management
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    token_type VARCHAR(20) DEFAULT 'refresh' NOT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent TEXT DEFAULT NULL,
    device_fingerprint VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ DEFAULT NULL,
    revoked_at TIMESTAMPTZ DEFAULT NULL
);

-- User activity logging
CREATE TABLE user_activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) DEFAULT NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) DEFAULT NULL,
    result VARCHAR(20) DEFAULT 'success' NOT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    user_agent TEXT DEFAULT NULL,
    request_id VARCHAR(36) DEFAULT NULL,
    extra_data TEXT DEFAULT NULL,
    error_message TEXT DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =============================================================================
-- USER PROFILE TABLES
-- =============================================================================

-- Main user profile
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,
    age INTEGER DEFAULT NULL,
    date_of_birth DATE DEFAULT NULL,
    gender VARCHAR(20) DEFAULT NULL,
    marital_status VARCHAR(50) DEFAULT NULL,
    state VARCHAR(100) DEFAULT NULL,
    country VARCHAR(100) DEFAULT 'USA',
    employment_status VARCHAR(50) DEFAULT NULL,
    occupation VARCHAR(100) DEFAULT NULL,
    risk_tolerance VARCHAR(20) DEFAULT NULL,
    retirement_age INTEGER DEFAULT 64,
    retirement_goal NUMERIC(12,2) DEFAULT 3500000,
    emergency_fund_months INTEGER DEFAULT 6,
    social_security_age INTEGER DEFAULT 67,
    social_security_monthly NUMERIC(12,2) DEFAULT 4000,
    risk_tolerance_score INTEGER DEFAULT 7,
    preferences JSON DEFAULT '{}',
    phone VARCHAR(20) DEFAULT NULL,
    address TEXT DEFAULT NULL,
    city VARCHAR(100) DEFAULT NULL,
    zip_code VARCHAR(20) DEFAULT NULL,
    emergency_contact VARCHAR(100) DEFAULT NULL,
    emergency_phone VARCHAR(20) DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- Family members
CREATE TABLE family_members (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES user_profiles(id) ON DELETE CASCADE NOT NULL,
    relationship_type VARCHAR(50) NOT NULL,
    name VARCHAR(100) DEFAULT NULL,
    age INTEGER DEFAULT NULL,
    date_of_birth DATE DEFAULT NULL,
    income NUMERIC(12,2) DEFAULT NULL,
    retirement_savings NUMERIC(12,2) DEFAULT NULL,
    education_fund_target NUMERIC(12,2) DEFAULT NULL,
    education_fund_current NUMERIC(12,2) DEFAULT NULL,
    expected_college_year INTEGER DEFAULT NULL,
    requires_financial_support BOOLEAN DEFAULT FALSE,
    monthly_support_amount NUMERIC(12,2) DEFAULT NULL,
    care_cost_estimate NUMERIC(12,2) DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- User benefits
CREATE TABLE user_benefits (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES user_profiles(id) ON DELETE CASCADE NOT NULL,
    benefit_type VARCHAR(50) NOT NULL,
    benefit_name VARCHAR(100) DEFAULT NULL,
    estimated_monthly_benefit NUMERIC(12,2) DEFAULT NULL,
    full_retirement_age INTEGER DEFAULT NULL,
    early_retirement_reduction NUMERIC(5,2) DEFAULT NULL,
    delayed_retirement_increase NUMERIC(5,2) DEFAULT NULL,
    spouse_benefit_eligible BOOLEAN DEFAULT FALSE,
    spouse_benefit_amount NUMERIC(12,2) DEFAULT NULL,
    pension_type VARCHAR(50) DEFAULT NULL,
    vesting_schedule VARCHAR(100) DEFAULT NULL,
    vested_percentage NUMERIC(5,2) DEFAULT NULL,
    expected_monthly_payout NUMERIC(12,2) DEFAULT NULL,
    lump_sum_option BOOLEAN DEFAULT FALSE,
    employer_match_percentage NUMERIC(5,2) DEFAULT NULL,
    employer_match_limit NUMERIC(12,2) DEFAULT NULL,
    health_insurance_premium NUMERIC(12,2) DEFAULT NULL,
    employer_contribution NUMERIC(12,2) DEFAULT NULL,
    benefit_start_date DATE DEFAULT NULL,
    benefit_end_date DATE DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- User tax information
CREATE TABLE user_tax_info (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES user_profiles(id) ON DELETE CASCADE NOT NULL,
    tax_year INTEGER DEFAULT EXTRACT(YEAR FROM NOW()) NOT NULL,
    filing_status VARCHAR(50) DEFAULT NULL,
    federal_tax_bracket NUMERIC(5,2) DEFAULT NULL,
    state_tax_bracket NUMERIC(5,2) DEFAULT NULL,
    effective_tax_rate NUMERIC(5,2) DEFAULT NULL,
    marginal_tax_rate NUMERIC(5,2) DEFAULT NULL,
    adjusted_gross_income NUMERIC(12,2) DEFAULT NULL,
    taxable_income NUMERIC(12,2) DEFAULT NULL,
    traditional_401k_contribution NUMERIC(12,2) DEFAULT NULL,
    roth_401k_contribution NUMERIC(12,2) DEFAULT NULL,
    traditional_ira_contribution NUMERIC(12,2) DEFAULT NULL,
    roth_ira_contribution NUMERIC(12,2) DEFAULT NULL,
    hsa_contribution NUMERIC(12,2) DEFAULT NULL,
    max_401k_contribution NUMERIC(12,2) DEFAULT NULL,
    max_ira_contribution NUMERIC(12,2) DEFAULT NULL,
    max_hsa_contribution NUMERIC(12,2) DEFAULT NULL,
    standard_deduction NUMERIC(12,2) DEFAULT NULL,
    itemized_deductions NUMERIC(12,2) DEFAULT NULL,
    tax_credits NUMERIC(12,2) DEFAULT NULL,
    has_tax_professional BOOLEAN DEFAULT FALSE,
    tax_professional_name VARCHAR(100) DEFAULT NULL,
    tax_strategy_notes TEXT DEFAULT NULL,
    estimated_quarterly_payments BOOLEAN DEFAULT FALSE,
    quarterly_payment_amount NUMERIC(12,2) DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- =============================================================================
-- FINANCIAL DATA TABLES
-- =============================================================================

-- Account Type Enum
CREATE TYPE account_type AS ENUM ('checking', 'savings', 'investment', 'retirement', 'credit', 'loan', 'mortgage', 'crypto');

-- Entry Category Enum
CREATE TYPE entry_category AS ENUM ('assets', 'liabilities', 'income', 'expenses');

-- Data Quality Enum
CREATE TYPE data_quality AS ENUM ('DQ1', 'DQ2', 'DQ3', 'DQ4');

-- Frequency Type Enum
CREATE TYPE frequency_type AS ENUM ('one_time', 'daily', 'weekly', 'monthly', 'quarterly', 'annually');

-- Financial accounts
CREATE TABLE financial_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    account_type account_type NOT NULL,
    institution_name VARCHAR(100) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_number_masked VARCHAR(20) DEFAULT NULL,
    plaid_account_id VARCHAR(100) DEFAULT NULL,
    plaid_item_id VARCHAR(100) DEFAULT NULL,
    external_account_id VARCHAR(100) DEFAULT NULL,
    data_quality data_quality DEFAULT 'DQ4' NOT NULL,
    last_sync_at TIMESTAMPTZ DEFAULT NULL,
    sync_frequency VARCHAR(20) DEFAULT 'daily' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_manual BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- Financial entries (transactions, balances, manual inputs)
CREATE TABLE financial_entries (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES financial_accounts(id) DEFAULT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    category entry_category NOT NULL,
    subcategory VARCHAR(50) DEFAULT NULL,
    description VARCHAR(255) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    frequency frequency_type DEFAULT 'one_time' NOT NULL,
    entry_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ DEFAULT NULL,
    data_quality data_quality DEFAULT 'DQ4' NOT NULL,
    confidence_score NUMERIC(3,2) DEFAULT 1.00 NOT NULL,
    source VARCHAR(50) DEFAULT 'manual' NOT NULL,
    external_transaction_id VARCHAR(100) DEFAULT NULL,
    plaid_transaction_id VARCHAR(100) DEFAULT NULL,
    -- Asset allocation columns
    stock_percentage INTEGER DEFAULT 0,
    bond_percentage INTEGER DEFAULT 0,
    cash_percentage INTEGER DEFAULT 0,
    other_percentage INTEGER DEFAULT 0,
    -- New 5-asset allocation system
    real_estate_percentage INTEGER DEFAULT 0,
    stocks_percentage INTEGER DEFAULT 0,
    bonds_percentage INTEGER DEFAULT 0,
    alternative_percentage INTEGER DEFAULT 0,
    -- Enhanced liability fields
    interest_rate NUMERIC(5,3) DEFAULT NULL,
    loan_term_months INTEGER DEFAULT NULL,
    remaining_months INTEGER DEFAULT NULL,
    minimum_payment NUMERIC(10,2) DEFAULT NULL,
    is_fixed_rate BOOLEAN DEFAULT TRUE,
    loan_start_date TIMESTAMPTZ DEFAULT NULL,
    original_amount NUMERIC(12,2) DEFAULT NULL,
    -- Calculated fields
    daily_interest_cost NUMERIC(10,2) DEFAULT NULL,
    total_interest_lifetime NUMERIC(10,2) DEFAULT NULL,
    payoff_date DATE DEFAULT NULL,
    -- Vector DB sync tracking
    last_synced_to_vector TIMESTAMPTZ DEFAULT NULL,
    -- Metadata
    details TEXT DEFAULT NULL,
    tags TEXT DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    loan_details TEXT DEFAULT NULL,
    -- Status
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_recurring BOOLEAN DEFAULT FALSE NOT NULL,
    is_estimate BOOLEAN DEFAULT FALSE NOT NULL,
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- Account balance snapshots
CREATE TABLE account_balances (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES financial_accounts(id) NOT NULL,
    balance NUMERIC(12,2) NOT NULL,
    available_balance NUMERIC(12,2) DEFAULT NULL,
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    balance_type VARCHAR(20) DEFAULT 'current' NOT NULL,
    as_of_date TIMESTAMPTZ NOT NULL,
    source_type VARCHAR(20) DEFAULT 'api' NOT NULL,
    data_quality data_quality DEFAULT 'DQ1' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Net worth snapshots
CREATE TABLE net_worth_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    total_assets NUMERIC(12,2) NOT NULL,
    total_liabilities NUMERIC(12,2) NOT NULL,
    net_worth NUMERIC(12,2) NOT NULL,
    liquid_assets NUMERIC(12,2) DEFAULT 0.00 NOT NULL,
    investment_assets NUMERIC(12,2) DEFAULT 0.00 NOT NULL,
    real_estate_assets NUMERIC(12,2) DEFAULT 0.00 NOT NULL,
    other_assets NUMERIC(12,2) DEFAULT 0.00 NOT NULL,
    calculation_method VARCHAR(20) DEFAULT 'sum' NOT NULL,
    confidence_score NUMERIC(3,2) DEFAULT 1.00 NOT NULL,
    data_quality_score VARCHAR(3) NOT NULL,
    snapshot_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =============================================================================
-- GOALS SYSTEM (V1 - Legacy)
-- =============================================================================

-- Goal Type Enum
CREATE TYPE goal_type AS ENUM ('early_retirement', 'home_purchase', 'education', 'emergency_fund', 'debt_payoff', 'custom');

-- Goal Status Enum
CREATE TYPE goal_status AS ENUM ('draft', 'active', 'achieved', 'paused', 'abandoned');

-- Action Priority Enum
CREATE TYPE action_priority AS ENUM ('low', 'medium', 'high', 'critical');

-- Action Status Enum
CREATE TYPE action_status AS ENUM ('pending', 'in_progress', 'completed', 'skipped');

-- Financial goals (V1)
CREATE TABLE financial_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    goal_type goal_type NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT NULL,
    target_amount NUMERIC(12,2) NOT NULL,
    current_amount NUMERIC(12,2) DEFAULT 0.00 NOT NULL,
    target_date TIMESTAMPTZ NOT NULL,
    parameters TEXT DEFAULT NULL,
    progress_percentage NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    monthly_target NUMERIC(12,2) DEFAULT NULL,
    feasibility_score NUMERIC(3,2) DEFAULT NULL,
    success_probability NUMERIC(3,2) DEFAULT NULL,
    risk_level VARCHAR(10) DEFAULT NULL,
    status goal_status DEFAULT 'draft' NOT NULL,
    priority INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NULL,
    achieved_at TIMESTAMPTZ DEFAULT NULL,
    last_analyzed_at TIMESTAMPTZ DEFAULT NULL
);

-- Goal scenarios
CREATE TABLE goal_scenarios (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER REFERENCES financial_goals(id) NOT NULL,
    scenario_name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT NULL,
    is_baseline BOOLEAN DEFAULT FALSE NOT NULL,
    assumptions TEXT NOT NULL,
    projected_end_value NUMERIC(12,2) DEFAULT NULL,
    projected_end_date TIMESTAMPTZ DEFAULT NULL,
    required_monthly_amount NUMERIC(12,2) DEFAULT NULL,
    success_probability NUMERIC(3,2) DEFAULT NULL,
    confidence_score NUMERIC(3,2) DEFAULT NULL,
    model_version VARCHAR(20) DEFAULT NULL,
    calculation_method VARCHAR(50) DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- Action plans
CREATE TABLE action_plans (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER REFERENCES financial_goals(id) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    target_value NUMERIC(12,2) DEFAULT NULL,
    target_percentage NUMERIC(5,2) DEFAULT NULL,
    frequency VARCHAR(20) DEFAULT NULL,
    priority action_priority DEFAULT 'medium' NOT NULL,
    impact_score NUMERIC(3,2) DEFAULT NULL,
    difficulty_score NUMERIC(3,2) DEFAULT NULL,
    target_start_date TIMESTAMPTZ DEFAULT NULL,
    target_completion_date TIMESTAMPTZ DEFAULT NULL,
    estimated_duration_days INTEGER DEFAULT NULL,
    status action_status DEFAULT 'pending' NOT NULL,
    completion_percentage NUMERIC(5,2) DEFAULT 0.00 NOT NULL,
    notes TEXT DEFAULT NULL,
    completion_notes TEXT DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NULL,
    started_at TIMESTAMPTZ DEFAULT NULL,
    completed_at TIMESTAMPTZ DEFAULT NULL
);

-- Goal milestones
CREATE TABLE goal_milestones (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER REFERENCES financial_goals(id) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT NULL,
    target_amount NUMERIC(12,2) NOT NULL,
    target_date TIMESTAMPTZ NOT NULL,
    current_amount NUMERIC(12,2) DEFAULT 0.00 NOT NULL,
    is_achieved BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    achieved_at TIMESTAMPTZ DEFAULT NULL
);

-- Goal performance metrics
CREATE TABLE goal_performance_metrics (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER REFERENCES financial_goals(id) NOT NULL,
    actual_amount NUMERIC(12,2) NOT NULL,
    target_amount NUMERIC(12,2) NOT NULL,
    variance_amount NUMERIC(12,2) NOT NULL,
    variance_percentage NUMERIC(5,2) NOT NULL,
    updated_target_date TIMESTAMPTZ DEFAULT NULL,
    updated_success_probability NUMERIC(3,2) DEFAULT NULL,
    days_ahead_behind INTEGER DEFAULT 0 NOT NULL,
    measurement_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =============================================================================
-- GOALS SYSTEM (V2 - Modern with UUID)
-- =============================================================================

-- Goals V2 with comprehensive tracking
CREATE TABLE goals (
    goal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    category VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    target_amount NUMERIC(18,2) NOT NULL,
    target_date DATE NOT NULL,
    priority INTEGER DEFAULT 3 NOT NULL,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    params JSONB DEFAULT '{}' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Goals history for audit trail
CREATE TABLE goals_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id UUID REFERENCES goals(goal_id) ON DELETE CASCADE NOT NULL,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_type VARCHAR(20) NOT NULL,
    reason VARCHAR(500) DEFAULT NULL,
    diff JSONB NOT NULL,
    actor VARCHAR(255) NOT NULL
);

-- Goal relationships
CREATE TABLE goal_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_goal_id UUID REFERENCES goals(goal_id) ON DELETE CASCADE NOT NULL,
    child_goal_id UUID REFERENCES goals(goal_id) ON DELETE CASCADE NOT NULL,
    relationship_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_goal_id, child_goal_id, relationship_type)
);

-- Goal progress tracking
CREATE TABLE goal_progress (
    progress_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    goal_id UUID REFERENCES goals(goal_id) ON DELETE CASCADE NOT NULL,
    current_amount NUMERIC(18,2) NOT NULL,
    percentage_complete NUMERIC(5,2) NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT DEFAULT NULL,
    source VARCHAR(50) DEFAULT 'manual' NOT NULL
);

-- User preferences V2
CREATE TABLE user_preferences (
    preference_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,
    risk_tolerance VARCHAR(20) DEFAULT 'moderate' NOT NULL,
    investment_timeline INTEGER DEFAULT 20 NOT NULL,
    financial_knowledge VARCHAR(20) DEFAULT 'intermediate' NOT NULL,
    retirement_age INTEGER DEFAULT NULL,
    annual_income_goal NUMERIC(18,2) DEFAULT NULL,
    emergency_fund_months INTEGER DEFAULT 6 NOT NULL,
    debt_payoff_priority VARCHAR(20) DEFAULT 'balanced' NOT NULL,
    notification_preferences JSONB DEFAULT '{}' NOT NULL,
    goal_categories_enabled JSONB DEFAULT '["retirement", "emergency_fund", "education", "real_estate"]' NOT NULL,
    -- Enhanced preference fields
    risk_score INTEGER DEFAULT NULL,
    investment_style VARCHAR(20) DEFAULT NULL,
    stocks_preference INTEGER DEFAULT NULL,
    bonds_preference INTEGER DEFAULT NULL,
    real_estate_preference INTEGER DEFAULT NULL,
    crypto_preference INTEGER DEFAULT NULL,
    retirement_lifestyle VARCHAR(20) DEFAULT NULL,
    work_flexibility JSONB DEFAULT '{}',
    esg_investing BOOLEAN DEFAULT FALSE,
    -- Tax-related fields
    tax_filing_status VARCHAR(30) DEFAULT NULL,
    federal_tax_bracket NUMERIC(5,4) DEFAULT NULL,
    state_tax_rate NUMERIC(5,4) DEFAULT NULL,
    state VARCHAR(2) DEFAULT NULL,
    tax_optimization_priority VARCHAR(20) DEFAULT NULL,
    tax_loss_harvesting BOOLEAN DEFAULT FALSE,
    roth_ira_eligible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- ANALYTICS AND ML TABLES
-- =============================================================================

-- Model Type Enum
CREATE TYPE model_type AS ENUM ('target_setting', 'portfolio_optimization', 'behavioral_prediction', 'gap_analysis', 'risk_assessment');

-- Prediction Status Enum
CREATE TYPE prediction_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- Interaction Type Enum
CREATE TYPE interaction_type AS ENUM ('page_view', 'button_click', 'form_submit', 'goal_create', 'goal_update', 'recommendation_view', 'recommendation_accept', 'recommendation_decline', 'calculation_request');

-- ML model predictions
CREATE TABLE model_predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    model_type model_type NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_name VARCHAR(100) DEFAULT NULL,
    input_data TEXT NOT NULL,
    input_hash VARCHAR(64) NOT NULL,
    output_data TEXT DEFAULT NULL,
    confidence_score NUMERIC(3,2) DEFAULT NULL,
    status prediction_status DEFAULT 'pending' NOT NULL,
    processing_time_ms INTEGER DEFAULT NULL,
    error_message TEXT DEFAULT NULL,
    context TEXT DEFAULT NULL,
    session_id VARCHAR(36) DEFAULT NULL,
    request_id VARCHAR(36) DEFAULT NULL,
    human_feedback_score NUMERIC(3,2) DEFAULT NULL,
    feedback_notes TEXT DEFAULT NULL,
    is_validated BOOLEAN DEFAULT FALSE NOT NULL,
    validation_date TIMESTAMPTZ DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ DEFAULT NULL
);

-- User interaction tracking
CREATE TABLE user_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) DEFAULT NULL,
    interaction_type interaction_type NOT NULL,
    page_url VARCHAR(500) DEFAULT NULL,
    element_id VARCHAR(100) DEFAULT NULL,
    element_text VARCHAR(200) DEFAULT NULL,
    session_id VARCHAR(36) NOT NULL,
    request_id VARCHAR(36) DEFAULT NULL,
    referrer_url VARCHAR(500) DEFAULT NULL,
    user_agent TEXT DEFAULT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    device_type VARCHAR(20) DEFAULT NULL,
    browser_name VARCHAR(50) DEFAULT NULL,
    screen_resolution VARCHAR(20) DEFAULT NULL,
    interaction_data TEXT DEFAULT NULL,
    duration_ms INTEGER DEFAULT NULL,
    scroll_depth INTEGER DEFAULT NULL,
    experiment_id VARCHAR(50) DEFAULT NULL,
    variant_id VARCHAR(50) DEFAULT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Model performance metrics
CREATE TABLE model_performance_metrics (
    id SERIAL PRIMARY KEY,
    model_type model_type NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    evaluation_date TIMESTAMPTZ NOT NULL,
    accuracy_score NUMERIC(5,4) DEFAULT NULL,
    precision_score NUMERIC(5,4) DEFAULT NULL,
    recall_score NUMERIC(5,4) DEFAULT NULL,
    f1_score NUMERIC(5,4) DEFAULT NULL,
    mae NUMERIC(10,4) DEFAULT NULL,
    mse NUMERIC(10,4) DEFAULT NULL,
    rmse NUMERIC(10,4) DEFAULT NULL,
    custom_metrics TEXT DEFAULT NULL,
    test_set_size INTEGER DEFAULT NULL,
    test_set_description VARCHAR(200) DEFAULT NULL,
    cross_validation_folds INTEGER DEFAULT NULL,
    evaluation_notes TEXT DEFAULT NULL,
    created_by VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Feature importance for model interpretability
CREATE TABLE feature_importance (
    id SERIAL PRIMARY KEY,
    model_type model_type NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_category VARCHAR(50) DEFAULT NULL,
    importance_score NUMERIC(8,6) NOT NULL,
    interpretation TEXT DEFAULT NULL,
    correlation_direction VARCHAR(10) DEFAULT NULL,
    calculation_method VARCHAR(50) NOT NULL,
    evaluation_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- A/B testing experiments
CREATE TABLE ab_test_experiments (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT NULL,
    hypothesis TEXT DEFAULT NULL,
    control_variant VARCHAR(50) NOT NULL,
    test_variants TEXT NOT NULL,
    traffic_allocation TEXT NOT NULL,
    primary_metric VARCHAR(100) NOT NULL,
    secondary_metrics TEXT DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'draft' NOT NULL,
    start_date TIMESTAMPTZ DEFAULT NULL,
    end_date TIMESTAMPTZ DEFAULT NULL,
    target_sample_size INTEGER DEFAULT NULL,
    results TEXT DEFAULT NULL,
    conclusion TEXT DEFAULT NULL,
    statistical_significance BOOLEAN DEFAULT NULL,
    created_by VARCHAR(100) NOT NULL,
    tags TEXT DEFAULT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- =============================================================================
-- PROJECTION SYSTEM TABLES
-- =============================================================================

-- Projection assumptions
CREATE TABLE projection_assumptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    -- Growth rates
    salary_growth_rate REAL DEFAULT 0.04 NOT NULL,
    rental_income_growth REAL DEFAULT 0.03 NOT NULL,
    business_income_growth REAL DEFAULT 0.06 NOT NULL,
    -- Asset appreciation rates
    real_estate_appreciation REAL DEFAULT 0.04 NOT NULL,
    stock_market_return REAL DEFAULT 0.08 NOT NULL,
    retirement_account_return REAL DEFAULT 0.065 NOT NULL,
    cash_equivalent_return REAL DEFAULT 0.02 NOT NULL,
    -- Expense growth factors
    inflation_rate REAL DEFAULT 0.025 NOT NULL,
    lifestyle_inflation REAL DEFAULT 0.01 NOT NULL,
    healthcare_inflation REAL DEFAULT 0.05 NOT NULL,
    -- Volatility parameters
    stock_volatility REAL DEFAULT 0.15 NOT NULL,
    real_estate_volatility REAL DEFAULT 0.02 NOT NULL,
    income_volatility REAL DEFAULT 0.05 NOT NULL,
    -- Tax considerations
    effective_tax_rate REAL DEFAULT 0.25 NOT NULL,
    capital_gains_rate REAL DEFAULT 0.15 NOT NULL,
    -- Advanced parameters
    rebalancing_frequency INTEGER DEFAULT 12 NOT NULL,
    sequence_risk_factor REAL DEFAULT 0.02 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NULL
);

-- Projection snapshots
CREATE TABLE projection_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    projection_years INTEGER NOT NULL,
    scenario_type VARCHAR(20) NOT NULL,
    projected_values JSON NOT NULL,
    confidence_intervals JSON NOT NULL,
    growth_components JSON NOT NULL,
    key_milestones JSON NOT NULL,
    assumptions_used JSON NOT NULL,
    monte_carlo_iterations INTEGER DEFAULT 1000 NOT NULL,
    calculation_time_ms INTEGER NOT NULL,
    starting_financials JSON NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Projection sensitivity analysis
CREATE TABLE projection_sensitivity (
    id SERIAL PRIMARY KEY,
    snapshot_id INTEGER REFERENCES projection_snapshots(id) NOT NULL,
    factor_name VARCHAR(50) NOT NULL,
    base_value REAL NOT NULL,
    sensitivity_results JSON NOT NULL,
    impact_ranking INTEGER NOT NULL,
    correlation_coefficient REAL NOT NULL,
    elasticity REAL NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- User and authentication indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX idx_user_activity_user_id ON user_activity_logs(user_id);
CREATE INDEX idx_user_activity_action ON user_activity_logs(action);

-- Profile indexes
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_family_members_profile_id ON family_members(profile_id);
CREATE INDEX idx_user_benefits_profile_id ON user_benefits(profile_id);
CREATE INDEX idx_user_tax_info_profile_id ON user_tax_info(profile_id);

-- Financial data indexes
CREATE INDEX idx_financial_accounts_user_id ON financial_accounts(user_id);
CREATE INDEX idx_financial_accounts_plaid ON financial_accounts(plaid_account_id);
CREATE INDEX idx_financial_entries_user_id ON financial_entries(user_id);
CREATE INDEX idx_financial_entries_account_id ON financial_entries(account_id);
CREATE INDEX idx_financial_entries_category ON financial_entries(category);
CREATE INDEX idx_financial_entries_date ON financial_entries(entry_date);
CREATE INDEX idx_account_balances_account_id ON account_balances(account_id);
CREATE INDEX idx_account_balances_date ON account_balances(as_of_date);
CREATE INDEX idx_net_worth_user_id ON net_worth_snapshots(user_id);
CREATE INDEX idx_net_worth_date ON net_worth_snapshots(snapshot_date);

-- Goals V1 indexes
CREATE INDEX idx_financial_goals_user_id ON financial_goals(user_id);
CREATE INDEX idx_financial_goals_type ON financial_goals(goal_type);
CREATE INDEX idx_financial_goals_status ON financial_goals(status);
CREATE INDEX idx_goal_scenarios_goal_id ON goal_scenarios(goal_id);
CREATE INDEX idx_action_plans_goal_id ON action_plans(goal_id);
CREATE INDEX idx_goal_milestones_goal_id ON goal_milestones(goal_id);
CREATE INDEX idx_goal_performance_goal_id ON goal_performance_metrics(goal_id);

-- Goals V2 indexes
CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_category ON goals(category);
CREATE INDEX idx_goals_target_date ON goals(target_date);
CREATE INDEX idx_goals_priority ON goals(priority);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_history_goal_id ON goals_history(goal_id);
CREATE INDEX idx_goals_history_changed_at ON goals_history(changed_at);
CREATE INDEX idx_goal_progress_goal_id ON goal_progress(goal_id);
CREATE INDEX idx_goal_progress_recorded_at ON goal_progress(recorded_at);
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- Analytics indexes
CREATE INDEX idx_model_predictions_user_id ON model_predictions(user_id);
CREATE INDEX idx_model_predictions_type ON model_predictions(model_type);
CREATE INDEX idx_model_predictions_hash ON model_predictions(input_hash);
CREATE INDEX idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX idx_user_interactions_type ON user_interactions(interaction_type);
CREATE INDEX idx_user_interactions_session ON user_interactions(session_id);
CREATE INDEX idx_user_interactions_timestamp ON user_interactions(timestamp);
CREATE INDEX idx_model_performance_type ON model_performance_metrics(model_type);
CREATE INDEX idx_model_performance_date ON model_performance_metrics(evaluation_date);
CREATE INDEX idx_feature_importance_type ON feature_importance(model_type);
CREATE INDEX idx_ab_experiments_id ON ab_test_experiments(experiment_id);

-- Projection indexes
CREATE INDEX idx_projection_assumptions_user_id ON projection_assumptions(user_id);
CREATE INDEX idx_projection_snapshots_user_id ON projection_snapshots(user_id);
CREATE INDEX idx_projection_sensitivity_snapshot_id ON projection_sensitivity(snapshot_id);

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================