/**
 * WealthPath AI - Comprehensive Summary Service Tests
 * Verifies ALL data elements including enhanced preferences are included
 */

import ComprehensiveSummaryService from '../ComprehensiveSummaryService';
import { ComprehensiveSummary, UserPreferences } from '../../types/financial.types';

// Mock comprehensive summary data based on data-final.md and database values
const mockComprehensiveSummary: ComprehensiveSummary = {
  user: {
    id: 1,
    name: "Debashish Roy",
    age: 54,
    email: "debashishroy@gmail.com",
    first_name: "Debashish",
    last_name: "Roy",
    is_active: true,
    status: "active",
    created_at: "2025-08-10T06:08:53.341584+00:00"
  },
  preferences: {
    // Basic preferences
    risk_tolerance: "moderate",
    investment_timeline: 20,
    financial_knowledge: "intermediate",
    retirement_age: 65,
    annual_income_goal: undefined,
    emergency_fund_months: 6,
    debt_payoff_priority: "balanced",
    notification_preferences: {},
    goal_categories_enabled: ["retirement", "education", "travel"],
    
    // Enhanced investment preferences
    risk_score: 7,
    investment_style: "aggressive",
    stocks_preference: 8,
    bonds_preference: 2,
    real_estate_preference: 5,
    crypto_preference: 1,
    retirement_lifestyle: "maintain",
    work_flexibility: {
      part_time: true,
      consulting: true,
      full_retirement: false
    },
    esg_investing: true,
    
    // Tax preferences
    tax_filing_status: "married_filing_jointly",
    federal_tax_bracket: 0.24,
    state_tax_rate: 0.04,
    state: "NC",
    tax_optimization_priority: "moderate",
    tax_loss_harvesting: true,
    roth_ira_eligible: true,
    
    created_at: "2025-08-14T15:06:16.700873+00:00",
    updated_at: "2025-08-18T05:07:16.921405+00:00"
  },
  financials: {
    netWorth: 2565545,
    totalAssets: 2879827,
    totalLiabilities: 314282,
    monthlyIncome: 17744,
    monthlyExpenses: 7124,
    monthlySurplus: 10620,
    savingsRate: 59.9,
    debtToIncomeRatio: 17.7,
    emergencyFundCoverage: 1.2,
    assets: {
      realEstate: [
        { name: "Primary Home", value: 1050000, subcategory: "real_estate" },
        { name: "Rental Property Uttara", value: 250000, subcategory: "real_estate" },
        { name: "Rental Property Bellagio", value: 91529, subcategory: "real_estate" },
        { name: "Rental Property Aashiyana", value: 58177, subcategory: "real_estate" }
      ],
      investments: [
        { name: "401K", value: 310216, subcategory: "retirement_accounts" },
        { name: "M1 Account", value: 315000, subcategory: "investment_accounts" },
        { name: "Mutual Funds Offshore", value: 138000, subcategory: "investment_accounts" },
        { name: "Bitcoin", value: 130000, subcategory: "investment_accounts" },
        { name: "Robinhood", value: 112000, subcategory: "investment_accounts" },
        { name: "eTrade", value: 76000, subcategory: "investment_accounts" },
        { name: "Pacific Life", value: 40000, subcategory: "investment_accounts" },
        { name: "HSA", value: 30000, subcategory: "investment_accounts" },
        { name: "Webull Ameritrade Fidelity", value: 30000, subcategory: "investment_accounts" }
      ],
      cash: [
        { name: "Money Market CapOne", value: 68705, subcategory: "cash_bank_accounts" },
        { name: "529 Education", value: 70488, subcategory: "other_assets" },
        { name: "Checking", value: 8506, subcategory: "cash_bank_accounts" },
        { name: "Savings", value: 764, subcategory: "cash_bank_accounts" },
        { name: "Emergency", value: 764, subcategory: "other_assets" }
      ],
      personalProperty: [
        { name: "Car", value: 43000, subcategory: "personal_property" },
        { name: "Jewelry", value: 30860, subcategory: "personal_property" }
      ]
    },
    liabilities: [
      { name: "Home Loan", balance: 313026, subcategory: "mortgage_real_estate", type: "mortgage" },
      { name: "Chase Credit Card 1613", balance: 971, subcategory: "credit_cards", type: "credit_card" },
      { name: "Credit Card 2038", balance: 285, subcategory: "credit_cards", type: "credit_card" }
    ],
    cashFlow: {
      monthlyIncome: 17744,
      monthlyExpenses: 7124,
      surplus: 10620
    },
    assetAllocation: {
      realEstate: { value: 1449706, percentage: 50.3 },
      investments: { value: 1181216, percentage: 41.0 },
      cash: { value: 139193, percentage: 4.8 },
      personalProperty: { value: 73860, percentage: 2.6 }
    }
  },
  goals: [
    {
      goal_id: "642c3ebc-1c72-40e6-9c38-4313c0334646",
      user_id: 1,
      category: "retirement",
      name: "Retirement Goal",
      target_amount: 3500000,
      target_date: "2035-12-31",
      priority: 3,
      status: "active",
      params: {
        current_age: 54,
        retirement_age: 65,
        annual_spending: 750000
      },
      yearsToGoal: 10.3,
      monthlyRequired: 12549.54,
      currentProgress: 310216,
      progressPercentage: 8.9
    },
    {
      goal_id: "a14331de-c441-47a4-af30-bdb24a79f210",
      user_id: 1,
      category: "education",
      name: "Son College",
      target_amount: 100000,
      target_date: "2027-05-05",
      priority: 3,
      status: "active",
      params: {
        start_year: 2027,
        degree_type: "undergraduate",
        institution_type: "public"
      },
      yearsToGoal: 2.7,
      monthlyRequired: 3086.42,
      currentProgress: 70488,
      progressPercentage: 70.5
    }
  ],
  recommendations: {
    portfolio_adjustment: "Based on your aggressive investment style and 8/10 stock preference, consider increasing equity allocation to 80%",
    risk_assessment: "Current 50.3% real estate concentration exceeds recommended 30% for moderate risk profile",
    tax_optimization: "As someone in the 24% federal bracket with tax loss harvesting enabled, consider municipal bonds for tax efficiency",
    next_steps: [
      "Increase emergency fund from 1.2 to 6 months expenses ($42,744)",
      "Consider maximizing Roth IRA contributions ($6,500 annual limit)",
      "Excellent savings rate! Consider tax-advantaged account optimization"
    ],
    warnings: [
      "Emergency fund below target of 6 months",
      "High concentration in real estate (50.3%)"
    ]
  },
  database_metadata: {
    total_tables: 30,
    total_financial_entries: 63,
    total_users: 1,
    last_updated: "2025-08-18T05:07:16.921405+00:00",
    data_quality_score: 85,
    calculation_method: "live_financial_entries"
  }
};

// Mock fetch implementation
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(() => 'mock-token'),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

describe('ComprehensiveSummaryService', () => {
  let service: ComprehensiveSummaryService;

  beforeEach(() => {
    service = ComprehensiveSummaryService.getInstance();
    jest.clearAllMocks();
  });

  describe('getComprehensiveSummary', () => {
    it('should return complete financial data with ALL preferences', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockComprehensiveSummary
      });

      const summary = await service.getComprehensiveSummary(1);

      // Verify financial data matches known values from data-final.md
      expect(summary.financials.netWorth).toBe(2565545);
      expect(summary.financials.monthlyIncome).toBe(17744);
      expect(summary.financials.monthlyExpenses).toBe(7124);
      expect(summary.financials.monthlySurplus).toBe(10620);
      expect(summary.financials.savingsRate).toBe(59.9);

      // Verify ALL basic preferences are included
      expect(summary.preferences).toBeDefined();
      expect(summary.preferences.risk_tolerance).toBe("moderate");
      expect(summary.preferences.investment_timeline).toBe(20);
      expect(summary.preferences.financial_knowledge).toBe("intermediate");
      expect(summary.preferences.emergency_fund_months).toBe(6);
      expect(summary.preferences.debt_payoff_priority).toBe("balanced");

      // Verify ALL enhanced preferences are included
      expect(summary.preferences.risk_score).toBe(7);
      expect(summary.preferences.investment_style).toBe("aggressive");
      expect(summary.preferences.stocks_preference).toBe(8);
      expect(summary.preferences.bonds_preference).toBe(2);
      expect(summary.preferences.real_estate_preference).toBe(5);
      expect(summary.preferences.crypto_preference).toBe(1);
      expect(summary.preferences.retirement_lifestyle).toBe("maintain");
      expect(summary.preferences.work_flexibility?.part_time).toBe(true);
      expect(summary.preferences.work_flexibility?.consulting).toBe(true);
      expect(summary.preferences.esg_investing).toBe(true);

      // Verify ALL tax preferences are included
      expect(summary.preferences.tax_filing_status).toBe("married_filing_jointly");
      expect(summary.preferences.federal_tax_bracket).toBe(0.24);
      expect(summary.preferences.state_tax_rate).toBe(0.04);
      expect(summary.preferences.state).toBe("NC");
      expect(summary.preferences.tax_optimization_priority).toBe("moderate");
      expect(summary.preferences.tax_loss_harvesting).toBe(true);
      expect(summary.preferences.roth_ira_eligible).toBe(true);

      // Verify structure matches comprehensive-summary.json
      expect(summary.financials.assets.realEstate).toHaveLength(4);
      expect(summary.financials.assets.investments).toHaveLength(9);
      expect(summary.financials.assets.cash).toHaveLength(5);
      expect(summary.financials.assets.personalProperty).toHaveLength(2);

      // Verify goals are included
      expect(summary.goals).toHaveLength(2);
      expect(summary.goals[0].name).toBe("Retirement Goal");
      expect(summary.goals[1].name).toBe("Son College");
    });

    it('should handle authentication errors', async () => {
      mockLocalStorage.getItem.mockReturnValueOnce(null);

      await expect(service.getComprehensiveSummary(1)).rejects.toThrow('Authentication token not found');
    });

    it('should handle API errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'User not found' })
      });

      await expect(service.getComprehensiveSummary(1)).rejects.toThrow('User not found');
    });
  });

  describe('formatForLLM', () => {
    it('should format correctly for LLM with ALL preferences', () => {
      const formatted = service.formatForLLM(mockComprehensiveSummary);

      // Verify all sections are included
      expect(formatted.userProfile).toContain('Debashish Roy');
      expect(formatted.userProfile).toContain('Age: 54');

      // Verify basic preferences are formatted
      expect(formatted.preferences).toContain('Risk Tolerance: moderate');
      expect(formatted.preferences).toContain('Investment Timeline: 20 years');
      expect(formatted.preferences).toContain('Financial Knowledge: intermediate');

      // Verify enhanced preferences are formatted
      expect(formatted.preferences).toContain('7/10 detailed score');
      expect(formatted.preferences).toContain('Investment Style: aggressive');
      expect(formatted.preferences).toContain('Stocks Preference: 8/10');
      expect(formatted.preferences).toContain('Bonds Preference: 2/10');
      expect(formatted.preferences).toContain('ESG/Sustainable Investing: Important');

      // Verify retirement planning section
      expect(formatted.preferences).toContain('Retirement Lifestyle: maintain');
      expect(formatted.preferences).toContain('Open to Part-time Work: Yes');
      expect(formatted.preferences).toContain('Open to Consulting: Yes');

      // Verify tax optimization section
      expect(formatted.preferences).toContain('Filing Status: married_filing_jointly');
      expect(formatted.preferences).toContain('Federal Tax Bracket: 24%');
      expect(formatted.preferences).toContain('State: NC (4.0% tax rate)');
      expect(formatted.preferences).toContain('Tax Loss Harvesting: Enabled');
      expect(formatted.preferences).toContain('Roth IRA Eligible: Yes');

      // Verify financial summary is formatted
      expect(formatted.financialSummary).toContain('NET WORTH: $2,565,545');
      expect(formatted.financialSummary).toContain('Monthly Surplus: $10,620');
      expect(formatted.financialSummary).toContain('Savings Rate: 59.9%');

      // Verify goals are formatted
      expect(formatted.goals).toContain('GOAL 1: Retirement Goal');
      expect(formatted.goals).toContain('GOAL 2: Son College');

      // Verify recommendations are formatted
      expect(formatted.recommendations).toContain('PORTFOLIO:');
      expect(formatted.recommendations).toContain('TAX OPTIMIZATION:');
      expect(formatted.recommendations).toContain('NEXT STEPS:');

      // Verify full context includes all sections
      expect(formatted.fullContext).toContain('USER PROFILE:');
      expect(formatted.fullContext).toContain('FINANCIAL PREFERENCES:');
      expect(formatted.fullContext).toContain('FINANCIAL SUMMARY:');
      expect(formatted.fullContext).toContain('GOALS & PROGRESS:');
      expect(formatted.fullContext).toContain('CURRENT RECOMMENDATIONS:');
    });

    it('should handle missing preference fields gracefully', () => {
      const incompletePreferences = {
        ...mockComprehensiveSummary,
        preferences: {
          risk_tolerance: "moderate",
          investment_timeline: 20,
          financial_knowledge: "intermediate",
          emergency_fund_months: 6,
          debt_payoff_priority: "balanced",
          notification_preferences: {},
          goal_categories_enabled: ["retirement"]
          // Missing enhanced and tax preferences
        } as UserPreferences
      };

      const formatted = service.formatForLLM(incompletePreferences);

      expect(formatted.preferences).toContain('Investment Style: Not specified');
      expect(formatted.preferences).toContain('Stocks Preference: N/A/10');
      expect(formatted.preferences).toContain('Federal Tax Bracket: Not specified');
    });
  });

  describe('validateDataQuality', () => {
    it('should validate complete data with high score', () => {
      const validation = service.validateDataQuality(mockComprehensiveSummary);

      expect(validation.isValid).toBe(true);
      expect(validation.errors).toHaveLength(0);
      expect(validation.score).toBeGreaterThan(80);
    });

    it('should detect missing user name', () => {
      const invalidSummary = {
        ...mockComprehensiveSummary,
        user: { ...mockComprehensiveSummary.user, name: 'User' }
      };

      const validation = service.validateDataQuality(invalidSummary);

      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Invalid or generic user name');
      expect(validation.score).toBeLessThan(100);
    });

    it('should detect missing preferences', () => {
      const invalidSummary = {
        ...mockComprehensiveSummary,
        preferences: undefined as any
      };

      const validation = service.validateDataQuality(invalidSummary);

      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('User preferences missing');
    });

    it('should warn about missing enhanced preferences', () => {
      const incompletePreferences = {
        ...mockComprehensiveSummary,
        preferences: {
          ...mockComprehensiveSummary.preferences,
          risk_score: undefined,
          investment_style: undefined,
          tax_filing_status: undefined,
          federal_tax_bracket: undefined
        }
      };

      const validation = service.validateDataQuality(incompletePreferences);

      expect(validation.warnings).toContain('Detailed risk score not set');
      expect(validation.warnings).toContain('Investment style not specified');
      expect(validation.warnings).toContain('Tax filing status not set');
      expect(validation.warnings).toContain('Federal tax bracket not specified');
    });

    it('should warn about high real estate concentration', () => {
      const highRealEstate = {
        ...mockComprehensiveSummary,
        financials: {
          ...mockComprehensiveSummary.financials,
          assetAllocation: {
            ...mockComprehensiveSummary.financials.assetAllocation,
            realEstate: { value: 2000000, percentage: 70 }
          }
        }
      };

      const validation = service.validateDataQuality(highRealEstate);

      expect(validation.warnings).toContain('Very high real estate concentration');
    });
  });

  describe('getQuickSummary', () => {
    it('should return simplified summary with key metrics', () => {
      const quickSummary = service.getQuickSummary(mockComprehensiveSummary);

      expect(quickSummary.netWorth).toBe(2565545);
      expect(quickSummary.monthlyIncome).toBe(17744);
      expect(quickSummary.monthlySurplus).toBe(10620);
      expect(quickSummary.savingsRate).toBe(59.9);
      expect(quickSummary.riskProfile).toBe('moderate (7/10)');
      expect(quickSummary.investmentStyle).toBe('aggressive');
      expect(quickSummary.taxBracket).toBe('24%');
      expect(quickSummary.dataQuality).toBe(85);
    });

    it('should handle missing preference values', () => {
      const incompletePreferences = {
        ...mockComprehensiveSummary,
        preferences: {
          ...mockComprehensiveSummary.preferences,
          risk_score: undefined,
          investment_style: undefined,
          federal_tax_bracket: undefined
        }
      };

      const quickSummary = service.getQuickSummary(incompletePreferences);

      expect(quickSummary.riskProfile).toBe('moderate (N/A/10)');
      expect(quickSummary.investmentStyle).toBe('Not specified');
      expect(quickSummary.taxBracket).toBe('Not specified');
    });
  });
});

// Integration test to verify API endpoint structure
describe('API Integration', () => {
  it('should match expected API response structure', () => {
    // This test verifies that our mock data matches the expected API structure
    const summary = mockComprehensiveSummary;

    // Verify top-level structure
    expect(summary).toHaveProperty('user');
    expect(summary).toHaveProperty('preferences');
    expect(summary).toHaveProperty('financials');
    expect(summary).toHaveProperty('goals');
    expect(summary).toHaveProperty('recommendations');
    expect(summary).toHaveProperty('database_metadata');

    // Verify preferences structure includes ALL fields
    expect(summary.preferences).toHaveProperty('risk_tolerance');
    expect(summary.preferences).toHaveProperty('risk_score');
    expect(summary.preferences).toHaveProperty('investment_style');
    expect(summary.preferences).toHaveProperty('stocks_preference');
    expect(summary.preferences).toHaveProperty('bonds_preference');
    expect(summary.preferences).toHaveProperty('real_estate_preference');
    expect(summary.preferences).toHaveProperty('crypto_preference');
    expect(summary.preferences).toHaveProperty('retirement_lifestyle');
    expect(summary.preferences).toHaveProperty('work_flexibility');
    expect(summary.preferences).toHaveProperty('esg_investing');
    expect(summary.preferences).toHaveProperty('tax_filing_status');
    expect(summary.preferences).toHaveProperty('federal_tax_bracket');
    expect(summary.preferences).toHaveProperty('state_tax_rate');
    expect(summary.preferences).toHaveProperty('state');
    expect(summary.preferences).toHaveProperty('tax_optimization_priority');
    expect(summary.preferences).toHaveProperty('tax_loss_harvesting');
    expect(summary.preferences).toHaveProperty('roth_ira_eligible');

    // Verify recommendations include preference-based advice
    expect(summary.recommendations).toHaveProperty('portfolio_adjustment');
    expect(summary.recommendations).toHaveProperty('risk_assessment');
    expect(summary.recommendations).toHaveProperty('tax_optimization');
    expect(summary.recommendations).toHaveProperty('next_steps');
    expect(summary.recommendations).toHaveProperty('warnings');
  });
});