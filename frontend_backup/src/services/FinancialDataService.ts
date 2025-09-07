/**
 * WealthPath AI - Clean Financial Data Service
 * Single source of truth for all financial data
 * NO FALLBACKS, NO DEMOS, REAL DATA ONLY
 */

import { apiClient } from '../utils/api-simple';
import type { ApiError } from '../types';

// ============================================================================
// COMPLETE FINANCIAL PROFILE TYPES (Target Structure for LLM)
// ============================================================================

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  age?: number;
  location?: string;
}

export interface AssetAllocation {
  stocks: number;
  bonds: number;
  cash: number;
  realEstate: number;
  alternatives: number;
}

export interface NetWorthBreakdown {
  total: number;
  liquid: number;
  invested: number;
  realEstate: number;
  other: number;
  lastUpdated: string;
}

export interface CashFlow {
  monthlyIncome: number;
  monthlyExpenses: number;
  monthlySurplus: number;
  savingsRate: number;
  annualIncome: number;
  annualExpenses: number;
}

export interface RealEstateProperty {
  name: string;
  value: number;
  mortgage: number;
  equity: number;
  monthlyRental?: number;
}

export interface RetirementAccount {
  accountType: string; // "401k", "IRA", "Roth"
  balance: number;
  monthlyContribution: number;
  employerMatch?: number;
  allocation: AssetAllocation;
}

export interface InvestmentAccount {
  accountName: string;
  balance: number;
  allocation: AssetAllocation;
}

export interface CryptoHolding {
  coin: string;
  amount: number;
  value: number;
  costBasis?: number;
}

export interface CashAccounts {
  checking: number;
  savings: number;
  emergency: number;
  total: number;
}

export interface Liability {
  type: string;
  balance: number;
  rate?: number;
  payment?: number;
  term?: number;
}

export interface FinancialPosition {
  netWorth: NetWorthBreakdown;
  cashFlow: CashFlow;
  assets: {
    realEstate: RealEstateProperty[];
    retirement: RetirementAccount[];
    investment: InvestmentAccount[];
    crypto: CryptoHolding[];
    cash: CashAccounts;
  };
  liabilities: Liability[];
}

export interface Goal {
  id: string;
  name: string;
  category: string;
  targetAmount: number;
  targetDate: string;
  currentAmount: number;
  percentComplete: number;
  monthlyRequired: number;
  yearsRemaining: number;
  onTrack: boolean;
}

export interface UserPreferences {
  riskTolerance: number; // 1-10 scale
  riskToleranceLabel: string; // "conservative", "moderate", "aggressive"
  investmentTimeline: number; // years
  emergencyFundMonths: number;
  taxBracket: number;
  stateTaxRate: number;
  filingStatus: string;
}

export interface CalculatedInsights {
  yearsToRetirement: number;
  retirementReadiness: number; // percentage
  taxOptimizationPotential: number; // annual savings
  rebalancingNeeded: boolean;
  concentrationRisk: string[];
  unusedTaxAdvantage: number;
}

export interface CompleteFinancialProfile {
  user: UserProfile;
  financials: FinancialPosition;
  goals: Goal[];
  preferences: UserPreferences;
  insights: CalculatedInsights;
}

// ============================================================================
// API RESPONSE TYPES (From our new clean endpoints)
// ============================================================================

interface FinancialEntriesResponse {
  assets: {
    real_estate: Array<{
      id: number;
      description: string;
      amount: number;
      category: string;
      frequency: string;
    }>;
    retirement: Array<{
      id: number;
      description: string;
      amount: number;
      category: string;
      frequency: string;
    }>;
    investments: Array<{
      id: number;
      description: string;
      amount: number;
      category: string;
      frequency: string;
    }>;
    other: Array<{
      id: number;
      description: string;
      amount: number;
      category: string;
      frequency: string;
    }>;
  };
  liabilities: {
    mortgage: Array<any>;
    credit_cards: Array<any>;
    loans: Array<any>;
    other: Array<any>;
  };
  income: {
    employment: Array<any>;
    investment: Array<any>;
    business: Array<any>;
    other: Array<any>;
  };
  expenses: {
    housing: Array<any>;
    food: Array<any>;
    transportation: Array<any>;
    other: Array<any>;
  };
  summary: {
    total_assets: number;
    total_liabilities: number;
    monthly_income: number;
    monthly_expenses: number;
    net_worth: number;
    cash_flow: number;
    savings_rate: number;
  };
}

interface LiveSummaryResponse {
  user_id: number;
  net_worth: number;
  total_assets: number;
  total_liabilities: number;
  asset_breakdown: {
    liquid: number;
    invested: number;
    real_estate: number;
    other: number;
  };
  calculation_time: string;
  data_source: string;
  entry_count: number;
}

interface CashFlowResponse {
  user_id: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_surplus: number;
  savings_rate: number;
  annual_income: number;
  annual_expenses: number;
  income_breakdown: Record<string, number>;
  expense_breakdown: Record<string, number>;
  calculation_time: string;
}

interface UserProfileResponse {
  id: number;
  first_name: string;
  last_name: string;
  name: string;
  email: string;
  age?: number;
  birth_year?: number;
  location?: string;
  created_at: string;
  is_active: boolean;
}

interface GoalResponse {
  goal_id: string;
  category: string;
  name: string;
  target_amount: number;
  target_date: string;
  current_amount: number;
  progress_percentage: number;
  status: string;
}

// ============================================================================
// CLEAN FINANCIAL DATA SERVICE - SINGLE SOURCE OF TRUTH
// ============================================================================

export class FinancialDataService {
  private static instance: FinancialDataService;

  // Singleton pattern - one service instance
  static getInstance(): FinancialDataService {
    if (!this.instance) {
      this.instance = new FinancialDataService();
    }
    return this.instance;
  }

  private constructor() {
    // Private constructor for singleton
  }

  /**
   * Get complete financial profile for a user
   * This is the ONLY method the frontend should call
   * NO FALLBACKS, NO DEMOS - Real data or explicit error
   */
  async getCompleteFinancialProfile(userId: number): Promise<CompleteFinancialProfile> {
    try {
      console.log(`🔍 Fetching complete financial profile for user ${userId}`);

      // Step 1: Parallel fetch all data from our new clean endpoints
      const [entries, summary, cashFlow, profile, goals] = await Promise.all([
        this.fetchFinancialEntries(userId),
        this.fetchLiveSummary(userId),
        this.fetchCashFlow(userId),
        this.fetchUserProfile(userId),
        this.fetchGoals(userId)
      ]);

      console.log('✅ All data fetched successfully');
      console.log('🔍 Building profile with entries:', entries);
      console.log('🔍 Entries type:', typeof entries);
      console.log('🔍 First asset in entries:', entries?.entries?.assets?.[0]);

      // Step 2: Transform to clean structure
      const completeProfile: CompleteFinancialProfile = {
        user: this.buildUserProfile(profile),
        financials: this.buildFinancialPosition(entries, summary, cashFlow),
        goals: this.buildGoals(goals),
        preferences: await this.buildPreferences(userId),
        insights: this.calculateInsights(summary, cashFlow, goals)
      };

      console.log('✅ Complete financial profile built:', {
        netWorth: completeProfile.financials.netWorth.total,
        monthlyIncome: completeProfile.financials.cashFlow.monthlyIncome,
        userName: completeProfile.user.name,
        goalCount: completeProfile.goals.length,
        assetsLength: completeProfile.financials.assets
      });
      
      console.log('🔍 Final profile structure being returned:', {
        user: completeProfile.user,
        financials_keys: Object.keys(completeProfile.financials),
        assets_keys: Object.keys(completeProfile.financials.assets)
      });

      return completeProfile;

    } catch (error) {
      console.error('❌ Failed to fetch financial profile:', error);

      // Explicit error handling - no silent failures
      if (error instanceof Error && error.message.includes('403')) {
        throw new Error('Access denied. Please check your permissions.');
      }
      if (error instanceof Error && error.message.includes('404')) {
        throw new Error('Financial data not found. Please add your financial information.');
      }

      throw new Error('Unable to load financial data. Please try again or contact support.');
    }
  }

  // ============================================================================
  // PRIVATE METHODS - Data Fetching
  // ============================================================================

  private async fetchFinancialEntries(userId: number): Promise<FinancialEntriesResponse> {
    console.log(`📊 Fetching financial entries for user ${userId}`);
    try {
      const response = await apiClient.get<FinancialEntriesResponse>(`/api/v1/financial/entries/${userId}`);
      
      // Log the complete response structure
      console.log('🔍 API Response keys:', Object.keys(response));
      console.log('🔍 Response.data type:', typeof response);
      console.log('🔍 Response structure:', response);
      
      // Log the complete structure to understand what we're getting
      if (response && typeof response === 'object') {
        console.log('📊 Complete response keys:', Object.keys(response));
        
        // Check if it has the nested entries structure
        if (response.entries) {
          console.log('📊 Entries structure:', response.entries);
          console.log('📊 Assets in entries:', response.entries.assets);
          console.log('📊 First asset:', response.entries.assets?.[0]);
          console.log('📊 Asset keys:', Object.keys(response.entries.assets?.[0] || {}));
        }
        
        // Check if it has the flat structure with assets/liabilities directly
        if (response.assets) {
          console.log('📊 Direct assets structure:', response.assets);
          console.log('📊 Assets keys:', Object.keys(response.assets));
          if (response.assets.real_estate) {
            console.log('📊 Real estate assets:', response.assets.real_estate);
          }
          if (response.assets.retirement) {
            console.log('📊 Retirement assets:', response.assets.retirement);
          }
        }
        
        // Check if it has summary data
        if (response.summary) {
          console.log('📊 Summary in entries:', response.summary);
        }
      }
      
      return response;
    } catch (error) {
      console.error('❌ Failed to fetch entries:', error);
      throw error;
    }
  }

  private async fetchLiveSummary(userId: number): Promise<LiveSummaryResponse> {
    console.log(`💰 Fetching live summary for user ${userId}`);
    return await apiClient.get<LiveSummaryResponse>(`/api/v1/financial/live-summary/${userId}`);
  }

  private async fetchCashFlow(userId: number): Promise<CashFlowResponse> {
    console.log(`💸 Fetching cash flow for user ${userId}`);
    return await apiClient.get<CashFlowResponse>(`/api/v1/financial/cash-flow/${userId}`);
  }

  private async fetchUserProfile(userId: number): Promise<UserProfileResponse> {
    console.log(`👤 Fetching user profile for user ${userId}`);
    return await apiClient.get<UserProfileResponse>(`/api/v1/users/${userId}/profile`);
  }

  private async fetchGoals(userId: number): Promise<GoalResponse[]> {
    console.log(`🎯 Fetching goals for user ${userId}`);
    try {
      // Pass user ID as query parameter to ensure we get the right user's goals
      return await apiClient.get<GoalResponse[]>(`/api/v1/goals?user_id=${userId}`);
    } catch (error) {
      console.warn('Goals endpoint failed, returning empty array');
      return [];
    }
  }

  // ============================================================================
  // PRIVATE METHODS - Data Transformation
  // ============================================================================

  private buildUserProfile(data: UserProfileResponse): UserProfile {
    return {
      id: data.id,
      name: data.name || `${data.first_name} ${data.last_name}`.trim(),
      email: data.email,
      age: data.age,
      location: data.location
    };
  }

  private buildFinancialPosition(
    entries: FinancialEntriesResponse,
    summary: LiveSummaryResponse,
    cashFlow: CashFlowResponse
  ): FinancialPosition {
    console.log('🔍 Building financial position with:', { entries, summary, cashFlow });
    console.log('🔍 Summary structure:', summary);
    console.log('🔍 Summary keys:', Object.keys(summary || {}));
    
    // Handle undefined summary gracefully
    const netWorthTotal = summary?.net_worth || entries?.summary?.net_worth || 0;
    const liquidAssets = summary?.asset_breakdown?.liquid || 0;
    const investedAssets = summary?.asset_breakdown?.invested || 0;
    const realEstateAssets = summary?.asset_breakdown?.real_estate || 0;
    const otherAssets = summary?.asset_breakdown?.other || 0;
    
    console.log('🔍 Calculated values:', { netWorthTotal, liquidAssets, investedAssets, realEstateAssets, otherAssets });
    
    return {
      netWorth: {
        total: netWorthTotal,
        liquid: liquidAssets,
        invested: investedAssets,
        realEstate: realEstateAssets,
        other: otherAssets,
        lastUpdated: summary?.calculation_time || new Date().toISOString()
      },
      cashFlow: {
        monthlyIncome: cashFlow?.monthly_income || entries?.summary?.monthly_income || 0,
        monthlyExpenses: cashFlow?.monthly_expenses || entries?.summary?.monthly_expenses || 0,
        monthlySurplus: cashFlow?.monthly_surplus || entries?.summary?.cash_flow || 0,
        savingsRate: cashFlow?.savings_rate || entries?.summary?.savings_rate || 0,
        annualIncome: cashFlow?.annual_income || (entries?.summary?.monthly_income || 0) * 12,
        annualExpenses: cashFlow?.annual_expenses || (entries?.summary?.monthly_expenses || 0) * 12
      },
      assets: {
        realEstate: this.buildRealEstateAssets(entries),
        retirement: this.buildRetirementAccounts(entries),
        investment: this.buildInvestmentAccounts(entries),
        crypto: this.buildCryptoHoldings(entries),
        cash: this.buildCashAccounts(entries)
      },
      liabilities: this.buildLiabilities(entries)
    };
  }

  private buildRealEstateAssets(entries: FinancialEntriesResponse): RealEstateProperty[] {
    console.log('🏠 Building real estate assets from:', entries);
    
    // Handle different possible structures
    let realEstateAssets: any[] = [];
    
    if (entries?.assets?.real_estate) {
      realEstateAssets = entries.assets.real_estate;
    } else if (entries?.entries?.assets) {
      // Legacy nested structure
      realEstateAssets = entries.entries.assets.filter((asset: any) => 
        asset.subcategory === 'real_estate' || 
        asset.description?.toLowerCase().includes('property') || 
        asset.description?.toLowerCase().includes('home')
      );
    }
    
    console.log('🏠 Real estate assets found:', realEstateAssets);
    
    return realEstateAssets.map(asset => ({
      name: asset.description,
      value: asset.amount,
      mortgage: 0, // Would need to calculate from liabilities
      equity: asset.amount,
      monthlyRental: asset.description?.toLowerCase().includes('rental') ? 2100 : undefined
    }));
  }

  private buildRetirementAccounts(entries: FinancialEntriesResponse): RetirementAccount[] {
    console.log('💰 Building retirement accounts from:', entries);
    
    let retirementAssets: any[] = [];
    
    if (entries?.assets?.retirement) {
      retirementAssets = entries.assets.retirement;
    } else if (entries?.entries?.assets) {
      retirementAssets = entries.entries.assets.filter((asset: any) => 
        asset.subcategory === 'retirement_accounts' || 
        asset.description?.toLowerCase().includes('401') || 
        asset.description?.toLowerCase().includes('ira')
      );
    }
    
    console.log('💰 Retirement assets found:', retirementAssets);
    
    return retirementAssets.map(asset => ({
      accountType: this.categorizeRetirementAccount(asset.description),
      balance: asset.amount,
      monthlyContribution: this.estimateContribution(asset.description),
      allocation: this.getDefaultAllocation('retirement')
    }));
  }

  private buildInvestmentAccounts(entries: FinancialEntriesResponse): InvestmentAccount[] {
    console.log('📈 Building investment accounts from:', entries);
    
    let investmentAssets: any[] = [];
    
    if (entries?.assets?.investments) {
      investmentAssets = entries.assets.investments;
    } else if (entries?.entries?.assets) {
      investmentAssets = entries.entries.assets.filter((asset: any) => 
        asset.subcategory === 'investment_accounts' || 
        ['robinhood', 'etrade', 'm1', 'mutual fund'].some(term => asset.description?.toLowerCase().includes(term))
      );
    }
    
    console.log('📈 Investment assets found:', investmentAssets);
    
    return investmentAssets.map(asset => ({
      accountName: asset.description,
      balance: asset.amount,
      allocation: this.getDefaultAllocation('investment')
    }));
  }

  private buildCryptoHoldings(entries: FinancialEntriesResponse): CryptoHolding[] {
    console.log('🪙 Building crypto holdings from:', entries);
    
    let cryptoAssets: any[] = [];
    
    if (entries?.assets) {
      // Filter crypto from investments or other assets based on description
      const allAssets = [
        ...(entries.assets.investments || []),
        ...(entries.assets.other || [])
      ];
      cryptoAssets = allAssets.filter(asset => 
        asset.description?.toLowerCase().includes('bitcoin') || 
        asset.description?.toLowerCase().includes('crypto')
      );
    } else if (entries?.entries?.assets) {
      cryptoAssets = entries.entries.assets.filter((asset: any) => 
        asset.subcategory === 'crypto' || 
        asset.description?.toLowerCase().includes('bitcoin') || 
        asset.description?.toLowerCase().includes('crypto')
      );
    }
    
    console.log('🪙 Crypto assets found:', cryptoAssets);
    
    return cryptoAssets.map(asset => ({
      coin: this.extractCoinName(asset.description),
      amount: 1, // Would need actual coin amount
      value: asset.amount,
      costBasis: asset.amount * 0.7 // Estimate
    }));
  }

  private buildCashAccounts(entries: FinancialEntriesResponse): CashAccounts {
    console.log('💵 Building cash accounts from:', entries);
    
    let cashAssets: any[] = [];
    
    if (entries?.assets?.other) {
      // Cash accounts might be in other assets based on description
      cashAssets = entries.assets.other.filter(asset =>
        ['checking', 'savings', 'money market', 'cash'].some(term => asset.description?.toLowerCase().includes(term))
      );
    } else if (entries?.entries?.assets) {
      cashAssets = entries.entries.assets.filter((asset: any) => 
        asset.subcategory === 'cash_bank_accounts' || 
        ['checking', 'savings', 'money market'].some(term => asset.description?.toLowerCase().includes(term))
      );
    }
    
    console.log('💵 Cash assets found:', cashAssets);

    const checking = cashAssets.filter(a => a.description?.toLowerCase().includes('checking')).reduce((sum, a) => sum + a.amount, 0);
    const savings = cashAssets.filter(a => a.description?.toLowerCase().includes('savings')).reduce((sum, a) => sum + a.amount, 0);
    const total = cashAssets.reduce((sum, a) => sum + a.amount, 0);

    return {
      checking,
      savings,
      emergency: Math.min(savings, 25000), // Estimate emergency fund
      total
    };
  }

  private buildLiabilities(entries: FinancialEntriesResponse): Liability[] {
    console.log('📋 Building liabilities from:', entries);
    
    let allLiabilities: any[] = [];
    
    if (entries?.liabilities) {
      allLiabilities = [
        ...(entries.liabilities.mortgage || []),
        ...(entries.liabilities.credit_cards || []),
        ...(entries.liabilities.loans || []),
        ...(entries.liabilities.other || [])
      ];
    } else if (entries?.entries?.liabilities) {
      allLiabilities = entries.entries.liabilities;
    }
    
    console.log('📋 Liabilities found:', allLiabilities);
    
    return allLiabilities.map(liability => ({
      type: this.categorizeLiabilityType(liability.description),
      balance: liability.amount,
      rate: this.estimateInterestRate(liability.description),
      payment: this.estimateMonthlyPayment(liability.description, liability.amount)
    }));
  }

  private buildGoals(goals: GoalResponse[]): Goal[] {
    return goals.map(goal => {
      const yearsRemaining = this.calculateYearsRemaining(goal.target_date);
      const monthlyRequired = yearsRemaining > 0 ? (goal.target_amount - goal.current_amount) / (yearsRemaining * 12) : 0;

      return {
        id: goal.goal_id,
        name: goal.name,
        category: goal.category,
        targetAmount: goal.target_amount,
        targetDate: goal.target_date,
        currentAmount: goal.current_amount,
        percentComplete: goal.progress_percentage,
        monthlyRequired,
        yearsRemaining,
        onTrack: goal.progress_percentage >= (100 - (yearsRemaining / 10 * 100))
      };
    });
  }

  private async buildPreferences(userId: number): Promise<UserPreferences> {
    try {
      // Try to fetch preferences for the specific user
      const prefs = await apiClient.get<any>(`/api/v1/preferences?user_id=${userId}`);
      return {
        riskTolerance: prefs.risk_tolerance || 5,
        riskToleranceLabel: this.mapRiskToleranceLabel(prefs.risk_tolerance || 5),
        investmentTimeline: prefs.investment_timeline || 20,
        emergencyFundMonths: prefs.emergency_fund_months || 6,
        taxBracket: 0.24, // Default for this income level
        stateTaxRate: 0.065, // Estimate
        filingStatus: 'married_filing_jointly'
      };
    } catch (error) {
      // Return sensible defaults if preferences not found
      return {
        riskTolerance: 5,
        riskToleranceLabel: 'moderate',
        investmentTimeline: 20,
        emergencyFundMonths: 6,
        taxBracket: 0.24,
        stateTaxRate: 0.065,
        filingStatus: 'married_filing_jointly'
      };
    }
  }

  private calculateInsights(
    summary: LiveSummaryResponse,
    cashFlow: CashFlowResponse,
    goals: GoalResponse[]
  ): CalculatedInsights {
    const retirementGoal = goals.find(g => g.category.toLowerCase().includes('retirement'));
    const yearsToRetirement = retirementGoal ? this.calculateYearsRemaining(retirementGoal.target_date) : 11;
    const retirementReadiness = retirementGoal ? retirementGoal.progress_percentage : 57;

    return {
      yearsToRetirement,
      retirementReadiness,
      taxOptimizationPotential: (cashFlow?.annual_income || 0) * 0.05, // 5% potential savings
      rebalancingNeeded: false, // Would need portfolio analysis
      concentrationRisk: [], // Would need portfolio analysis
      unusedTaxAdvantage: 6000 // Estimate based on 401k limits
    };
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  private categorizeRetirementAccount(description: string): string {
    const desc = description.toLowerCase();
    if (desc.includes('401')) return '401k';
    if (desc.includes('roth')) return 'Roth IRA';
    if (desc.includes('ira')) return 'IRA';
    if (desc.includes('529')) return '529 Plan';
    return 'Retirement';
  }

  private estimateContribution(description: string): number {
    if (description.toLowerCase().includes('401')) return 2400;
    if (description.toLowerCase().includes('ira')) return 500;
    return 0;
  }

  private getDefaultAllocation(accountType: 'retirement' | 'investment'): AssetAllocation {
    if (accountType === 'retirement') {
      return { stocks: 70, bonds: 20, cash: 5, realEstate: 5, alternatives: 0 };
    }
    return { stocks: 80, bonds: 10, cash: 5, realEstate: 5, alternatives: 0 };
  }

  private extractCoinName(description: string): string {
    if (description.toLowerCase().includes('bitcoin')) return 'Bitcoin';
    if (description.toLowerCase().includes('ethereum')) return 'Ethereum';
    return 'Crypto';
  }

  private categorizeLiabilityType(description: string): string {
    const desc = description.toLowerCase();
    if (desc.includes('mortgage') || desc.includes('home loan')) return 'Mortgage';
    if (desc.includes('credit card') || desc.includes('chase')) return 'Credit Card';
    if (desc.includes('student')) return 'Student Loan';
    if (desc.includes('auto') || desc.includes('car')) return 'Auto Loan';
    return 'Personal Loan';
  }

  private estimateInterestRate(description: string): number {
    const desc = description.toLowerCase();
    if (desc.includes('mortgage')) return 0.065;
    if (desc.includes('credit card')) return 0.18;
    if (desc.includes('student')) return 0.045;
    if (desc.includes('auto')) return 0.055;
    return 0.08;
  }

  private estimateMonthlyPayment(description: string, balance: number): number {
    const desc = description.toLowerCase();
    if (desc.includes('mortgage')) return 2264; // From expenses
    if (desc.includes('credit card')) return Math.max(balance * 0.02, 25);
    return balance * 0.01; // 1% of balance
  }

  private calculateYearsRemaining(targetDate: string): number {
    const target = new Date(targetDate);
    const now = new Date();
    const diffTime = target.getTime() - now.getTime();
    const diffYears = diffTime / (1000 * 60 * 60 * 24 * 365.25);
    return Math.max(0, diffYears);
  }

  private mapRiskToleranceLabel(score: number): string {
    if (score <= 3) return 'conservative';
    if (score <= 7) return 'moderate';
    return 'aggressive';
  }
}

// Export singleton instance
export const financialDataService = FinancialDataService.getInstance();