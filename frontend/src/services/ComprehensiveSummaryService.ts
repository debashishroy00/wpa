/**
 * WealthPath AI - Comprehensive Summary Service
 * Service for fetching complete financial summaries with ALL preferences data
 */

import { 
  ComprehensiveSummary, 
  ValidationResult, 
  LLMContext, 
  UserPreferences 
} from '../types/financial.types';

class ComprehensiveSummaryService {
  private static instance: ComprehensiveSummaryService;
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  }

  static getInstance(): ComprehensiveSummaryService {
    if (!this.instance) {
      this.instance = new ComprehensiveSummaryService();
    }
    return this.instance;
  }

  /**
   * Get DTI status indicator based on debt-to-income ratio
   */
  static getDTIStatus(dti: number): { label: string; color: string; icon: string; description: string } {
    if (dti < 20) return { 
      label: 'Excellent', 
      color: 'green', 
      icon: '🟢',
      description: 'Very low debt burden - excellent financial health'
    };
    if (dti < 36) return { 
      label: 'Good', 
      color: 'yellow', 
      icon: '🟡',
      description: 'Manageable debt levels - within recommended range'
    };
    if (dti < 50) return { 
      label: 'Fair', 
      color: 'orange', 
      icon: '🟠',
      description: 'High debt burden - consider debt reduction strategies'
    };
    return { 
      label: 'High', 
      color: 'red', 
      icon: '🔴',
      description: 'Very high debt burden - immediate attention needed'
    };
  }

  /**
   * Get comprehensive financial summary with ALL preference data
   */
  async getComprehensiveSummary(userId: number): Promise<ComprehensiveSummary> {
    try {
      const authTokens = localStorage.getItem('auth_tokens');
      if (!authTokens) {
        throw new Error('Authentication token not found');
      }
      
      const tokens = JSON.parse(authTokens);
      const token = tokens.access_token;
      if (!token) {
        throw new Error('Access token not found');
      }

      const response = await fetch(`${this.baseURL}/api/v1/financial/comprehensive-summary/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Validate the response structure
      const validation = this.validateDataQuality(data);
      if (!validation.isValid) {
        console.warn('Data quality issues detected:', validation.errors);
      }

      return data;
    } catch (error) {
      console.error('Failed to fetch comprehensive summary:', error);
      throw error;
    }
  }

  /**
   * Format comprehensive summary for LLM consumption with ALL preferences
   */
  formatForLLM(summary: ComprehensiveSummary): LLMContext {
    const userProfile = this.formatUserProfile(summary.user);
    const preferences = this.formatPreferences(summary.preferences);
    const financialSummary = this.formatFinancials(summary.financials);
    const goals = this.formatGoals(summary.goals);
    const recommendations = this.formatRecommendations(summary.recommendations);

    const fullContext = `
USER PROFILE:
${userProfile}

FINANCIAL PREFERENCES:
${preferences}

FINANCIAL SUMMARY:
${financialSummary}

GOALS & PROGRESS:
${goals}

CURRENT RECOMMENDATIONS:
${recommendations}

DATA QUALITY: Score ${summary.database_metadata.data_quality_score}/100
LAST UPDATED: ${summary.database_metadata.last_updated}
CALCULATION METHOD: ${summary.database_metadata.calculation_method}
`.trim();

    return {
      userProfile,
      preferences,
      financialSummary,
      goals,
      recommendations,
      fullContext
    };
  }

  /**
   * Format user profile section
   */
  private formatUserProfile(user: any): string {
    return `
- Name: ${user.name}
- Age: ${user.age}
- Email: ${user.email}
- Account Status: ${user.status}
`.trim();
  }

  /**
   * Format ALL user preferences including enhanced and tax fields
   */
  private formatPreferences(prefs: UserPreferences): string {
    const sections = [];

    // Basic Financial Preferences
    sections.push(`BASIC PREFERENCES:
- Risk Tolerance: ${prefs.risk_tolerance} (${prefs.risk_score || 'N/A'}/10 detailed score)
- Investment Timeline: ${prefs.investment_timeline} years
- Financial Knowledge: ${prefs.financial_knowledge}
- Emergency Fund Target: ${prefs.emergency_fund_months} months
- Debt Strategy: ${prefs.debt_payoff_priority}`);

    // Enhanced Investment Preferences
    if (prefs.investment_style || prefs.stocks_preference || prefs.bonds_preference) {
      sections.push(`INVESTMENT PREFERENCES:
- Investment Style: ${prefs.investment_style || 'Not specified'}
- Stocks Preference: ${prefs.stocks_preference || 'N/A'}/10
- Bonds Preference: ${prefs.bonds_preference || 'N/A'}/10  
- Real Estate Preference: ${prefs.real_estate_preference || 'N/A'}/10
- Crypto Preference: ${prefs.crypto_preference || 'N/A'}/10
- ESG/Sustainable Investing: ${prefs.esg_investing ? 'Important' : 'Not specified'}`);
    }

    // Retirement Planning
    if (prefs.retirement_lifestyle || prefs.work_flexibility) {
      const workFlex = prefs.work_flexibility || {};
      sections.push(`RETIREMENT PLANNING:
- Retirement Lifestyle: ${prefs.retirement_lifestyle || 'Not specified'}
- Open to Part-time Work: ${workFlex.part_time ? 'Yes' : 'No'}
- Open to Consulting: ${workFlex.consulting ? 'Yes' : 'No'}
- Target Retirement Age: ${prefs.retirement_age || 'Not specified'}`);
    }

    // Tax Optimization
    if (prefs.tax_filing_status || prefs.federal_tax_bracket) {
      const federalBracket = prefs.federal_tax_bracket ? `${(prefs.federal_tax_bracket * 100).toFixed(0)}%` : 'Not specified';
      const stateRate = prefs.state_tax_rate ? `${(prefs.state_tax_rate * 100).toFixed(1)}%` : 'Not specified';
      
      sections.push(`TAX OPTIMIZATION:
- Filing Status: ${prefs.tax_filing_status || 'Not specified'}
- Federal Tax Bracket: ${federalBracket}
- State: ${prefs.state || 'Not specified'} (${stateRate} tax rate)
- Tax Optimization Priority: ${prefs.tax_optimization_priority || 'Not specified'}
- Tax Loss Harvesting: ${prefs.tax_loss_harvesting ? 'Enabled' : 'Disabled'}
- Roth IRA Eligible: ${prefs.roth_ira_eligible ? 'Yes' : 'No'}`);
    }

    // Goal Categories
    if (prefs.goal_categories_enabled && prefs.goal_categories_enabled.length > 0) {
      sections.push(`GOAL CATEGORIES: ${prefs.goal_categories_enabled.join(', ')}`);
    }

    return sections.join('\n\n');
  }

  /**
   * Format financial summary section
   */
  private formatFinancials(financials: any): string {
    return `
NET WORTH: $${financials.netWorth.toLocaleString()}
- Total Assets: $${financials.totalAssets.toLocaleString()}
- Total Liabilities: $${financials.totalLiabilities.toLocaleString()}

CASH FLOW:
- Monthly Income: $${financials.monthlyIncome.toLocaleString()}
- Monthly Expenses: $${financials.monthlyExpenses.toLocaleString()}
- Monthly Surplus: $${financials.monthlySurplus.toLocaleString()}
- Savings Rate: ${financials.savingsRate}%

KEY RATIOS:
- Debt-to-Income Ratio: ${financials.debtToIncomeRatio}%
- Emergency Fund Coverage: ${financials.emergencyFundCoverage} months

ASSET ALLOCATION:
- Real Estate: ${financials.assetAllocation.realEstate.percentage}% ($${financials.assetAllocation.realEstate.value.toLocaleString()})
- Investments: ${financials.assetAllocation.investments.percentage}% ($${financials.assetAllocation.investments.value.toLocaleString()})
- Cash: ${financials.assetAllocation.cash.percentage}% ($${financials.assetAllocation.cash.value.toLocaleString()})
- Personal Property: ${financials.assetAllocation.personalProperty.percentage}% ($${financials.assetAllocation.personalProperty.value.toLocaleString()})

MAJOR ASSETS:
${this.formatAssetList(financials.assets)}

LIABILITIES:
${financials.liabilities.map((l: any) => `- ${l.name}: $${l.balance.toLocaleString()}`).join('\n')}
`.trim();
  }

  /**
   * Format asset lists
   */
  private formatAssetList(assets: any): string {
    const sections = [];
    
    if (assets.realEstate && assets.realEstate.length > 0) {
      sections.push(`Real Estate:\n${assets.realEstate.map((a: any) => `  - ${a.name}: $${a.value.toLocaleString()}`).join('\n')}`);
    }
    
    if (assets.investments && assets.investments.length > 0) {
      sections.push(`Investments:\n${assets.investments.map((a: any) => `  - ${a.name}: $${a.value.toLocaleString()}`).join('\n')}`);
    }
    
    if (assets.cash && assets.cash.length > 0) {
      sections.push(`Cash & Liquid:\n${assets.cash.map((a: any) => `  - ${a.name}: $${a.value.toLocaleString()}`).join('\n')}`);
    }
    
    return sections.join('\n\n');
  }

  /**
   * Format goals section
   */
  private formatGoals(goals: any[]): string {
    if (!goals || goals.length === 0) {
      return 'No active goals defined';
    }

    return goals.map((goal, index) => `
GOAL ${index + 1}: ${goal.name}
- Category: ${goal.category}
- Target: $${goal.target_amount.toLocaleString()} by ${goal.target_date}
- Current Progress: $${goal.currentProgress.toLocaleString()} (${goal.progressPercentage}%)
- Monthly Required: $${goal.monthlyRequired.toLocaleString()}
- Years Remaining: ${goal.yearsToGoal}
`).join('\n');
  }

  /**
   * Format recommendations section
   */
  private formatRecommendations(recommendations: any): string {
    const sections = [];

    if (recommendations.portfolio_adjustment) {
      sections.push(`PORTFOLIO: ${recommendations.portfolio_adjustment}`);
    }

    if (recommendations.risk_assessment) {
      sections.push(`RISK ASSESSMENT: ${recommendations.risk_assessment}`);
    }

    if (recommendations.tax_optimization) {
      sections.push(`TAX OPTIMIZATION: ${recommendations.tax_optimization}`);
    }

    if (recommendations.next_steps && recommendations.next_steps.length > 0) {
      sections.push(`NEXT STEPS:\n${recommendations.next_steps.map((step: string) => `- ${step}`).join('\n')}`);
    }

    if (recommendations.warnings && recommendations.warnings.length > 0) {
      sections.push(`WARNINGS:\n${recommendations.warnings.map((warning: string) => `⚠️ ${warning}`).join('\n')}`);
    }

    return sections.join('\n\n');
  }

  /**
   * Validate data quality of comprehensive summary
   */
  validateDataQuality(summary: ComprehensiveSummary): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    let score = 100;

    // Check user profile completeness
    if (!summary.user || !summary.user.name || summary.user.name === 'User') {
      errors.push('Invalid or generic user name');
      score -= 20;
    }

    // Check financial data validity
    if (!summary.financials || summary.financials.netWorth === 0) {
      errors.push('Net worth is zero or missing');
      score -= 30;
    }

    if (summary.financials && summary.financials.monthlyIncome === 0) {
      errors.push('Monthly income is zero');
      score -= 20;
    }

    // Check preferences completeness
    if (!summary.preferences) {
      errors.push('User preferences missing');
      score -= 25;
    } else {
      // Check for enhanced preferences
      if (!summary.preferences.risk_score) {
        warnings.push('Detailed risk score not set');
        score -= 5;
      }

      if (!summary.preferences.investment_style) {
        warnings.push('Investment style not specified');
        score -= 5;
      }

      if (!summary.preferences.tax_filing_status) {
        warnings.push('Tax filing status not set');
        score -= 10;
      }

      if (!summary.preferences.federal_tax_bracket) {
        warnings.push('Federal tax bracket not specified');
        score -= 10;
      }
    }

    // Check goals
    if (!summary.goals || summary.goals.length === 0) {
      warnings.push('No financial goals defined');
      score -= 10;
    }

    // Check asset allocation reasonableness
    if (summary.financials && summary.financials.assetAllocation) {
      const allocation = summary.financials.assetAllocation;
      if (allocation.realEstate.percentage > 60) {
        warnings.push('Very high real estate concentration');
        score -= 5;
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      score: Math.max(0, score)
    };
  }

  /**
   * Get simplified summary for quick display
   */
  getQuickSummary(summary: ComprehensiveSummary): any {
    return {
      netWorth: summary.financials.netWorth,
      monthlyIncome: summary.financials.monthlyIncome,
      monthlySurplus: summary.financials.monthlySurplus,
      savingsRate: summary.financials.savingsRate,
      riskProfile: `${summary.preferences.risk_tolerance} (${summary.preferences.risk_score || 'N/A'}/10)`,
      investmentStyle: summary.preferences.investment_style || 'Not specified',
      taxBracket: summary.preferences.federal_tax_bracket ? `${(summary.preferences.federal_tax_bracket * 100).toFixed(0)}%` : 'Not specified',
      dataQuality: summary.database_metadata.data_quality_score
    };
  }
}

export default ComprehensiveSummaryService;