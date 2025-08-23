/**
 * WealthPath AI - Financial Data Types
 */

export enum AccountType {
  CHECKING = 'checking',
  SAVINGS = 'savings',
  INVESTMENT = 'investment',
  RETIREMENT = 'retirement',
  CREDIT = 'credit',
  LOAN = 'loan',
  MORTGAGE = 'mortgage',
  CRYPTO = 'crypto'
}

export enum EntryCategory {
  ASSETS = 'assets',
  LIABILITIES = 'liabilities',
  INCOME = 'income',
  EXPENSES = 'expenses',
  PROFILE = 'profile',
  BENEFITS = 'benefits',
  TAX_INFO = 'tax_info'
}

export enum DataQuality {
  DQ1 = 'DQ1', // Real-time API data
  DQ2 = 'DQ2', // Daily API sync
  DQ3 = 'DQ3', // Manual entry with validation
  DQ4 = 'DQ4'  // Manual entry, unverified
}

export enum FrequencyType {
  ONE_TIME = 'one_time',
  DAILY = 'daily',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  ANNUALLY = 'annually'
}

export interface FinancialEntry {
  id: string;
  user_id: number;
  category: EntryCategory;
  subcategory?: string;
  description: string;
  amount: number;
  currency: string;
  frequency: FrequencyType;
  entry_date: string;
  notes?: string;
  // Asset allocation (new 5-category system)
  real_estate_percentage?: number;
  stocks_percentage?: number;
  bonds_percentage?: number;
  cash_percentage?: number;
  alternative_percentage?: number;
  
  // Enhanced liability fields
  interest_rate?: number;
  loan_term_months?: number;
  remaining_months?: number;
  minimum_payment?: number;
  is_fixed_rate?: boolean;
  loan_start_date?: string;
  original_amount?: number;
  loan_details?: string;
  
  data_quality: DataQuality;
  confidence_score: number;
  source: string;
  is_active: boolean;
  is_recurring: boolean;
  created_at: string;
  updated_at?: string;
}

export interface FinancialEntryCreate {
  category: EntryCategory;
  subcategory?: string;
  description: string;
  amount: number;
  currency?: string;
  frequency?: FrequencyType;
  entry_date?: string;
  notes?: string;
  // Asset allocation
  real_estate_percentage?: number;
  stocks_percentage?: number;
  bonds_percentage?: number;
  cash_percentage?: number;
  alternative_percentage?: number;
  
  // Enhanced liability fields
  interest_rate?: number;
  loan_term_months?: number;
  remaining_months?: number;
  minimum_payment?: number;
  is_fixed_rate?: boolean;
  loan_start_date?: string;
  original_amount?: number;
  loan_details?: string;
}

export interface FinancialEntryUpdate {
  description?: string;
  amount?: number;
  frequency?: FrequencyType;
  subcategory?: string;
  notes?: string;
  // Asset allocation
  real_estate_percentage?: number;
  stocks_percentage?: number;
  bonds_percentage?: number;
  cash_percentage?: number;
  alternative_percentage?: number;
  
  // Enhanced liability fields
  interest_rate?: number;
  loan_term_months?: number;
  remaining_months?: number;
  minimum_payment?: number;
  is_fixed_rate?: boolean;
  loan_start_date?: string;
  original_amount?: number;
  loan_details?: string;
}

export interface FinancialAccount {
  id: number;
  user_id: number;
  account_type: AccountType;
  institution_name: string;
  account_name: string;
  account_number_masked?: string;
  data_quality: DataQuality;
  last_sync_at?: string;
  is_active: boolean;
  is_manual: boolean;
  created_at: string;
}

export interface AccountBalance {
  id: number;
  account_id: number;
  balance: number;
  available_balance?: number;
  currency: string;
  balance_type: string;
  as_of_date: string;
  source_type: string;
  data_quality: DataQuality;
}

export interface FinancialSummary {
  user_id: number;
  net_worth: number;
  total_assets: number;
  total_liabilities: number;
  last_updated: string;
  data_quality_score: DataQuality;
  liquid_assets?: number;
  investment_assets?: number;
  real_estate_assets?: number;
  other_assets?: number;
  connected_accounts: number;
  manual_entries: number;
  net_worth_change?: number;
  net_worth_change_percentage?: number;
}

export interface NetWorthSnapshot {
  id: number;
  user_id: number;
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  liquid_assets: number;
  investment_assets: number;
  real_estate_assets: number;
  other_assets: number;
  confidence_score: number;
  data_quality_score: DataQuality;
  snapshot_date: string;
}

export interface DataQualityBreakdown {
  overall_score: DataQuality;
  total_entries: number;
  data_quality_breakdown: Record<DataQuality, number>;
  by_category: Record<EntryCategory, Record<DataQuality, number>>;
  by_source: Record<string, Record<DataQuality, number>>;
  recommendations: string[];
}

export interface DataSync {
  message: string;
  sync_id: string;
  accounts_to_sync: number;
  estimated_completion: string;
}

// API Response wrapper types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

// Filter and query types
export interface FinancialEntryFilters {
  category?: EntryCategory;
  data_quality?: DataQuality;
  limit?: number;
  offset?: number;
}

export interface NetWorthHistoryQuery {
  days?: number;
}

// Projection types
export interface ProjectionAssumptions {
  salary_growth: number;
  real_estate: number;
  stock_returns: number;
  retirement_401k: number;
  inflation: number;
}

export interface MonteCarloResults {
  mean: number;
  median: number;
  standard_deviation: number;
  percentiles: {
    p10: number;
    p25: number;
    p75: number;
    p90: number;
  };
  confidence_intervals: {
    ci_80: [number, number];
    ci_90: [number, number];
  };
}

export interface ProjectionScenario {
  scenario_type: string;
  years: number[];
  adjustments?: Record<string, any>;
}

export interface ProjectionResponse {
  scenario_projection: MonteCarloResults;
  assumptions: ProjectionAssumptions;
  years_projected: number[];
}

// UI State types
export interface FinancialUIState {
  isLoading: boolean;
  error?: string;
  selectedEntry?: FinancialEntry;
  isCreateModalOpen: boolean;
  isEditModalOpen: boolean;
  filters: FinancialEntryFilters;
}