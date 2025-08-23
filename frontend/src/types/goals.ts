/**
 * WealthPath AI - Goal Management Types
 */

export interface Goal {
  goal_id: string;
  user_id: number;
  category: string;
  name: string;
  target_amount: number;
  target_date: string;
  priority: number;
  status: string;
  params: Record<string, any>;
  created_at: string;
  updated_at: string;
  
  // Computed fields
  progress_percentage?: number;
  current_amount?: number;
  days_until_target?: number;
}

export interface GoalCreate {
  category: string;
  name: string;
  target_amount: number;
  target_date: string;
  priority?: number;
  params?: Record<string, any>;
}

export interface GoalUpdate {
  name?: string;
  target_amount?: number;
  target_date?: string;
  priority?: number;
  status?: string;
  params?: Record<string, any>;
  change_reason?: string;
}

export interface GoalProgress {
  progress_id: string;
  goal_id: string;
  current_amount: number;
  percentage_complete: number;
  recorded_at: string;
  notes?: string;
  source: string;
}

export interface GoalProgressCreate {
  current_amount: number;
  notes?: string;
}

export interface UserPreferences {
  preference_id: string;
  user_id: number;
  risk_tolerance: string;
  investment_timeline: number;
  financial_knowledge: string;
  retirement_age?: number;
  annual_income_goal?: number;
  emergency_fund_months: number;
  debt_payoff_priority: string;
  notification_preferences: Record<string, any>;
  goal_categories_enabled: string[];
  
  // Enhanced preference fields
  risk_score?: number;
  investment_style?: string;
  stocks_preference?: number;
  bonds_preference?: number;
  real_estate_preference?: number;
  crypto_preference?: number;
  retirement_lifestyle?: string;
  work_flexibility?: Record<string, any>;
  esg_investing?: boolean;
  
  // Tax-related fields
  tax_filing_status?: string;
  federal_tax_bracket?: number;
  state_tax_rate?: number;
  state?: string;
  tax_optimization_priority?: string;
  tax_loss_harvesting?: boolean;
  roth_ira_eligible?: boolean;
  
  created_at: string;
  updated_at: string;
}

export interface UserPreferencesUpdate {
  risk_tolerance?: string;
  investment_timeline?: number;
  financial_knowledge?: string;
  retirement_age?: number;
  annual_income_goal?: number;
  emergency_fund_months?: number;
  debt_payoff_priority?: string;
  notification_preferences?: Record<string, any>;
  goal_categories_enabled?: string[];
  
  // Enhanced preference fields
  risk_score?: number;
  investment_style?: string;
  stocks_preference?: number;
  bonds_preference?: number;
  real_estate_preference?: number;
  crypto_preference?: number;
  retirement_lifestyle?: string;
  work_flexibility?: Record<string, any>;
  esg_investing?: boolean;
  
  // Tax-related fields
  tax_filing_status?: string;
  federal_tax_bracket?: number;
  state_tax_rate?: number;
  state?: string;
  tax_optimization_priority?: string;
  tax_loss_harvesting?: boolean;
  roth_ira_eligible?: boolean;
}

export interface GoalConflict {
  goal1_id: string;
  goal1_name: string;
  goal2_id: string;
  goal2_name: string;
  conflict_type: string;
  severity: string;
}

export interface GoalSummary {
  active_goals: number;
  achieved_goals: number;
  total_target: number;
  nearest_deadline?: string;
  average_progress: number;
}

export interface GoalHistory {
  history_id: string;
  changed_at: string;
  change_type: string;
  reason?: string;
  diff: Record<string, any>;
  actor: string;
}

export interface GoalCategory {
  name: string;
  description: string;
  required_params: string[];
  typical_timeline: string;
}

export interface GoalTemplate {
  name: string;
  category: string;
  description: string;
  template_params: Record<string, any>;
}

export const GOAL_CATEGORIES = {
  retirement: 'Retirement',
  education: 'Education', 
  real_estate: 'Real Estate',
  business: 'Business',
  travel: 'Travel',
  emergency_fund: 'Emergency Fund',
  debt_payoff: 'Debt Payoff',
  major_purchase: 'Major Purchase',
  other: 'Other'
} as const;

export const GOAL_STATUSES = {
  active: 'Active',
  paused: 'Paused',
  achieved: 'Achieved',
  cancelled: 'Cancelled'
} as const;

export const RISK_TOLERANCE_LEVELS = {
  conservative: 'Conservative',
  moderate: 'Moderate',
  aggressive: 'Aggressive'
} as const;

export const FINANCIAL_KNOWLEDGE_LEVELS = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced'
} as const;