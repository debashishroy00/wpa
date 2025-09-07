/**
 * WealthPath AI - Complete Financial Types
 * Comprehensive interfaces for all financial data including enhanced user preferences
 */

// User Profile
export interface UserProfile {
  id: number;
  name: string;
  age: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  status: string;
  created_at?: string;
}

// Complete User Preferences including ALL enhanced fields
export interface UserPreferences {
  // Basic preferences
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  investment_timeline: number;
  financial_knowledge: 'beginner' | 'intermediate' | 'advanced';
  retirement_age?: number;
  annual_income_goal?: number;
  emergency_fund_months: number;
  debt_payoff_priority: 'avalanche' | 'snowball' | 'balanced';
  notification_preferences: Record<string, any>;
  goal_categories_enabled: string[];
  
  // Enhanced investment preferences
  risk_score?: number; // 1-10 scale
  investment_style?: 'conservative' | 'moderate' | 'aggressive';
  stocks_preference?: number; // 1-10 scale
  bonds_preference?: number; // 1-10 scale
  real_estate_preference?: number; // 1-10 scale
  crypto_preference?: number; // 1-10 scale
  retirement_lifestyle?: 'downsize' | 'maintain' | 'upgrade';
  work_flexibility?: {
    part_time?: boolean;
    consulting?: boolean;
    full_retirement?: boolean;
  };
  esg_investing?: boolean;
  
  // Tax preferences
  tax_filing_status?: 'single' | 'married_filing_jointly' | 'married_filing_separately' | 'head_of_household' | 'qualifying_widow';
  federal_tax_bracket?: number; // Decimal (0.24 = 24%)
  state_tax_rate?: number; // Decimal (0.065 = 6.5%)
  state?: string; // 2-letter state code
  tax_optimization_priority?: 'aggressive' | 'moderate' | 'conservative' | 'none';
  tax_loss_harvesting?: boolean;
  roth_ira_eligible?: boolean;
  
  // Timestamps
  created_at?: string;
  updated_at?: string;
}

// Asset Items
export interface AssetItem {
  name: string;
  value: number;
  subcategory: string;
}

// Liability Items
export interface LiabilityItem {
  name: string;
  balance: number;
  subcategory: string;
  type: string;
}

// Cash Flow Details
export interface CashFlowDetails {
  monthlyIncome: number;
  monthlyExpenses: number;
  surplus: number;
  incomeBreakdown?: IncomeItem[];
  expenseBreakdown?: ExpenseItem[];
}

export interface IncomeItem {
  source: string;
  amount: number;
  frequency: string;
  subcategory: string;
}

export interface ExpenseItem {
  category: string;
  amount: number;
  description: string;
  subcategory: string;
}

// Asset Allocation
export interface AllocationBreakdown {
  realEstate: {
    value: number;
    percentage: number;
  };
  investments: {
    value: number;
    percentage: number;
  };
  cash: {
    value: number;
    percentage: number;
  };
  personalProperty: {
    value: number;
    percentage: number;
  };
}

// Goal Progress
export interface GoalProgress {
  goal_id: string;
  user_id: number;
  category: string;
  name: string;
  target_amount: number;
  target_date: string;
  priority: number;
  status: string;
  params: Record<string, any>;
  yearsToGoal: number;
  monthlyRequired: number;
  currentProgress: number;
  progressPercentage: number;
}

// Personalized Recommendations based on preferences
export interface PersonalizedRecommendations {
  portfolio_adjustment: string;
  risk_assessment: string;
  tax_optimization: string;
  next_steps: string[];
  warnings: string[];
}

// Database Metadata
export interface MetadataInfo {
  total_tables: number;
  total_financial_entries: number;
  total_users: number;
  last_updated: string;
  data_quality_score: number;
  calculation_method: string;
  known_issues?: string[];
}

// Financial Summary
export interface FinancialSummary {
  netWorth: number;
  totalAssets: number;
  totalLiabilities: number;
  monthlyIncome: number;
  monthlyExpenses: number;
  monthlySurplus: number;
  savingsRate: number;
  debtToIncomeRatio: number;
  emergencyFundCoverage: number;
  assets: {
    realEstate: AssetItem[];
    investments: AssetItem[];
    cash: AssetItem[];
    personalProperty: AssetItem[];
  };
  liabilities: LiabilityItem[];
  cashFlow: CashFlowDetails;
  assetAllocation: AllocationBreakdown;
}

// Main Comprehensive Summary Interface
export interface ComprehensiveSummary {
  user: UserProfile;
  preferences: UserPreferences; // Complete preferences with all enhanced fields
  financials: FinancialSummary;
  goals: GoalProgress[];
  recommendations: PersonalizedRecommendations; // Personalized based on preferences
  database_metadata: MetadataInfo;
}

// Validation Result
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  score: number;
}

// LLM Context Format
export interface LLMContext {
  userProfile: string;
  preferences: string;
  financialSummary: string;
  goals: string;
  recommendations: string;
  fullContext: string;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
  timestamp: string;
}