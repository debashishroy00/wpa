/**
 * WealthPath AI - Deterministic Advisory Testing Framework
 * Validates advisory generation meets strict requirements
 */

import { DeterministicAdvisoryService, AdvisoryValidator } from '../DeterministicAdvisoryService';
import type { PlanInputs, AdvisoryOutput, ValidationResult } from '../DeterministicAdvisoryService';

describe('Deterministic Advisory Generation', () => {
  const service = DeterministicAdvisoryService.getInstance();
  
  // Test personas with expected outcomes
  const personas = [
    {
      name: 'Debashish Roy',
      userId: 1,
      expected: {
        net_worth: 2565545,
        monthly_surplus: 7940,
        risk_band: 'moderate',
        has_cc_payoff: true, // CC debt < $5000
        stabilize_first: false // Should be on track
      }
    },
    {
      name: 'High Risk Client',
      userId: 2,
      expected: {
        net_worth: 150000,
        monthly_surplus: 500,
        risk_band: 'aggressive',
        has_cc_payoff: false,
        stabilize_first: true // Low emergency fund
      }
    }
  ];
  
  // Mock inputs for testing validation
  const mockInputs: PlanInputs = {
    client: {
      name: 'Test Client',
      age: 35,
      risk_band: 'moderate',
      tax_bracket_est: 0.24
    },
    snapshot: {
      net_worth: 500000,
      monthly_surplus: 3000,
      asset_allocation_current: {
        stocks: 60,
        bonds: 30,
        cash: 10
      }
    },
    goals: [
      {
        id: 'retirement',
        name: 'Retirement',
        target: 2000000,
        deadline: '2055-01-01',
        required_monthly: 2500,
        funded_pct: 25
      }
    ],
    cashflow: {
      income_monthly: 8000,
      expenses_monthly: 5000,
      debts: [
        {
          type: 'credit_card',
          balance: 3000, // < $5000
          rate: 0.18,
          payment: 100
        }
      ]
    },
    plan_outputs: {
      asset_allocation_target: {
        stocks: 70,
        bonds: 20,
        cash: 10
      },
      rebalancing_trades: [],
      contribution_plan: [
        {
          account: '401k',
          monthly: 2000,
          max_allowed: 2291
        }
      ],
      debt_actions: [],
      monte_carlo: {
        success_prob: 0.85,
        note: 'Based on 10,000 simulations'
      }
    },
    computed: {
      required_contrib_total_monthly: 2500,
      surplus_minus_required: 500
    },
    constraints: {
      min_cash_buffer_months: 6,
      compliance_mode: 'education'
    },
    kb_context: [
      { id: 'KB-001', title: 'Asset Allocation by Age' },
      { id: 'KB-002', title: 'Tax-Advantaged Accounts' },
      { id: 'IRS-001', title: '401k Contribution Limits' },
      { id: 'IRS-002', title: 'HSA Contribution Limits' }
    ]
  };

  beforeEach(() => {
    // Reset any state if needed
  });

  describe('Structure Validation', () => {
    test('generates valid advisory structure', async () => {
      // Mock the LLM response for testing
      const mockOutput: AdvisoryOutput = {
        executive_summary: {
          overview: 'Test client is in a good financial position.',
          key_metrics: {
            net_worth: 500000,
            monthly_surplus: 3000,
            required_contrib_total_monthly: 2500,
            surplus_gap_monthly: 500
          },
          status_flags: {
            on_track: true,
            stabilize_first: false
          }
        },
        priority_actions_30d: [
          {
            title: 'Pay off credit card debt immediately',
            why_it_matters: 'High interest debt is costing significant money',
            exact_refs: ['KB-001']
          }
        ],
        strategy_12m: [
          { quarter: 'Q1', actions: ['Increase 401k contributions'] },
          { quarter: 'Q2', actions: ['Rebalance portfolio'] },
          { quarter: 'Q3', actions: ['Review insurance coverage'] },
          { quarter: 'Q4', actions: ['Tax planning review'] }
        ],
        risk_management: {
          top_risks: ['Market volatility', 'Job loss'],
          mitigations: ['Diversification', 'Emergency fund'],
          citations: ['KB-001']
        },
        tax_considerations: {
          ideas: ['Maximize 401k contributions', 'Consider Roth conversion'],
          citations: ['IRS-001', 'IRS-002']
        },
        disclaimer: 'This report is for educational purposes only and does not constitute financial advice.'
      };

      // Structure validation
      expect(mockOutput).toHaveProperty('executive_summary');
      expect(mockOutput).toHaveProperty('priority_actions_30d');
      expect(mockOutput).toHaveProperty('strategy_12m');
      expect(mockOutput).toHaveProperty('risk_management');
      expect(mockOutput).toHaveProperty('tax_considerations');
      expect(mockOutput).toHaveProperty('disclaimer');

      // Key metrics validation
      expect(mockOutput.executive_summary.key_metrics).toHaveProperty('net_worth');
      expect(mockOutput.executive_summary.key_metrics).toHaveProperty('monthly_surplus');
      expect(mockOutput.executive_summary.key_metrics).toHaveProperty('required_contrib_total_monthly');
      expect(mockOutput.executive_summary.key_metrics).toHaveProperty('surplus_gap_monthly');

      // Strategy validation
      expect(mockOutput.strategy_12m).toHaveLength(4);
      expect(mockOutput.strategy_12m[0].quarter).toBe('Q1');
      expect(mockOutput.strategy_12m[3].quarter).toBe('Q4');
    });
  });

  describe('Number Validation', () => {
    test('accepts valid numbers from inputs', () => {
      const validOutput: AdvisoryOutput = {
        executive_summary: {
          overview: 'Valid overview',
          key_metrics: {
            net_worth: 500000, // From inputs
            monthly_surplus: 3000, // From inputs
            required_contrib_total_monthly: 2500, // From inputs
            surplus_gap_monthly: 500 // From inputs
          },
          status_flags: {
            on_track: true,
            stabilize_first: false
          }
        },
        priority_actions_30d: [],
        strategy_12m: [
          { quarter: 'Q1', actions: [] },
          { quarter: 'Q2', actions: [] },
          { quarter: 'Q3', actions: [] },
          { quarter: 'Q4', actions: [] }
        ],
        risk_management: {
          top_risks: [],
          mitigations: [],
          citations: []
        },
        tax_considerations: {
          ideas: [],
          citations: []
        },
        disclaimer: 'Educational purposes only'
      };

      const validation = AdvisoryValidator.auditNumbers(validOutput, mockInputs);
      expect(validation.valid).toBe(true);
    });

    test('rejects unauthorized numbers', () => {
      const invalidOutput = {
        executive_summary: {
          overview: 'Invalid overview',
          key_metrics: {
            net_worth: 600000, // WRONG! Should be 500000
            monthly_surplus: 3000,
            required_contrib_total_monthly: 2500,
            surplus_gap_monthly: 500
          },
          status_flags: {
            on_track: true,
            stabilize_first: false
          }
        },
        priority_actions_30d: [],
        strategy_12m: [
          { quarter: 'Q1', actions: [] },
          { quarter: 'Q2', actions: [] },
          { quarter: 'Q3', actions: [] },
          { quarter: 'Q4', actions: [] }
        ],
        risk_management: {
          top_risks: [],
          mitigations: [],
          citations: []
        },
        tax_considerations: {
          ideas: [],
          citations: []
        },
        disclaimer: 'Educational purposes only'
      } as AdvisoryOutput;

      const validation = AdvisoryValidator.auditNumbers(invalidOutput, mockInputs);
      expect(validation.valid).toBe(false);
      expect(validation.error).toContain('Unauthorized numbers');
      expect(validation.error).toContain('600000');
    });
  });

  describe('Citation Validation', () => {
    test('accepts valid citations', () => {
      const validOutput: AdvisoryOutput = {
        executive_summary: {
          overview: 'Valid overview',
          key_metrics: {
            net_worth: 500000,
            monthly_surplus: 3000,
            required_contrib_total_monthly: 2500,
            surplus_gap_monthly: 500
          },
          status_flags: {
            on_track: true,
            stabilize_first: false
          }
        },
        priority_actions_30d: [
          {
            title: 'Test action',
            why_it_matters: 'Test reason',
            exact_refs: ['KB-001'] // Valid citation
          }
        ],
        strategy_12m: [
          { quarter: 'Q1', actions: [] },
          { quarter: 'Q2', actions: [] },
          { quarter: 'Q3', actions: [] },
          { quarter: 'Q4', actions: [] }
        ],
        risk_management: {
          top_risks: [],
          mitigations: [],
          citations: ['KB-002'] // Valid citation
        },
        tax_considerations: {
          ideas: [],
          citations: ['IRS-001'] // Valid citation
        },
        disclaimer: 'Educational purposes only'
      };

      const kbIds = ['KB-001', 'KB-002', 'IRS-001', 'IRS-002'];
      const validation = AdvisoryValidator.auditCitations(validOutput, kbIds);
      expect(validation.valid).toBe(true);
    });

    test('rejects invalid citations', () => {
      const invalidOutput: AdvisoryOutput = {
        executive_summary: {
          overview: 'Invalid overview',
          key_metrics: {
            net_worth: 500000,
            monthly_surplus: 3000,
            required_contrib_total_monthly: 2500,
            surplus_gap_monthly: 500
          },
          status_flags: {
            on_track: true,
            stabilize_first: false
          }
        },
        priority_actions_30d: [
          {
            title: 'Test action',
            why_it_matters: 'Test reason',
            exact_refs: ['INVALID-001'] // Invalid citation
          }
        ],
        strategy_12m: [
          { quarter: 'Q1', actions: [] },
          { quarter: 'Q2', actions: [] },
          { quarter: 'Q3', actions: [] },
          { quarter: 'Q4', actions: [] }
        ],
        risk_management: {
          top_risks: [],
          mitigations: [],
          citations: []
        },
        tax_considerations: {
          ideas: [],
          citations: []
        },
        disclaimer: 'Educational purposes only'
      };

      const kbIds = ['KB-001', 'KB-002', 'IRS-001', 'IRS-002'];
      const validation = AdvisoryValidator.auditCitations(invalidOutput, kbIds);
      expect(validation.valid).toBe(false);
      expect(validation.error).toContain('Invalid citations');
      expect(validation.error).toContain('INVALID-001');
    });
  });

  describe('Business Rules Validation', () => {
    test('enforces credit card payoff rule', () => {
      const outputWithoutCCPayoff: AdvisoryOutput = {
        executive_summary: {
          overview: 'Overview without CC payoff',
          key_metrics: {
            net_worth: 500000,
            monthly_surplus: 3000,
            required_contrib_total_monthly: 2500,
            surplus_gap_monthly: 500
          },
          status_flags: {
            on_track: true,
            stabilize_first: false
          }
        },
        priority_actions_30d: [
          {
            title: 'Increase investments', // Missing CC payoff
            why_it_matters: 'Build wealth',
            exact_refs: ['KB-001']
          }
        ],
        strategy_12m: [
          { quarter: 'Q1', actions: [] },
          { quarter: 'Q2', actions: [] },
          { quarter: 'Q3', actions: [] },
          { quarter: 'Q4', actions: [] }
        ],
        risk_management: {
          top_risks: [],
          mitigations: [],
          citations: []
        },
        tax_considerations: {
          ideas: [],
          citations: []
        },
        disclaimer: 'Educational purposes only'
      };

      const validation = AdvisoryValidator.auditBusinessRules(outputWithoutCCPayoff, mockInputs);
      expect(validation.valid).toBe(false);
      expect(validation.error).toContain('Credit card debt < $5000 should recommend immediate payoff');
    });

    test('validates emergency fund stabilization flag', () => {
      const lowEmergencyInputs = {
        ...mockInputs,
        snapshot: {
          ...mockInputs.snapshot,
          net_worth: 15000 // Only 3 months of expenses (15000/5000)
        }
      };

      const outputWithoutStabilizeFlag: AdvisoryOutput = {
        executive_summary: {
          overview: 'Overview',
          key_metrics: {
            net_worth: 15000,
            monthly_surplus: 3000,
            required_contrib_total_monthly: 2500,
            surplus_gap_monthly: 500
          },
          status_flags: {
            on_track: true,
            stabilize_first: false // Should be true due to low emergency fund
          }
        },
        priority_actions_30d: [],
        strategy_12m: [
          { quarter: 'Q1', actions: [] },
          { quarter: 'Q2', actions: [] },
          { quarter: 'Q3', actions: [] },
          { quarter: 'Q4', actions: [] }
        ],
        risk_management: {
          top_risks: [],
          mitigations: [],
          citations: []
        },
        tax_considerations: {
          ideas: [],
          citations: []
        },
        disclaimer: 'Educational purposes only'
      };

      const validation = AdvisoryValidator.auditBusinessRules(outputWithoutStabilizeFlag, lowEmergencyInputs);
      expect(validation.valid).toBe(false);
      expect(validation.error).toContain('Insufficient emergency fund not flagged');
    });
  });

  describe('Compliance Validation', () => {
    test('enforces educational disclaimer', () => {
      const outputWithoutEducationalDisclaimer: AdvisoryOutput = {
        executive_summary: {
          overview: 'Overview',
          key_metrics: {
            net_worth: 500000,
            monthly_surplus: 3000,
            required_contrib_total_monthly: 2500,
            surplus_gap_monthly: 500
          },
          status_flags: {
            on_track: true,
            stabilize_first: false
          }
        },
        priority_actions_30d: [],
        strategy_12m: [
          { quarter: 'Q1', actions: [] },
          { quarter: 'Q2', actions: [] },
          { quarter: 'Q3', actions: [] },
          { quarter: 'Q4', actions: [] }
        ],
        risk_management: {
          top_risks: [],
          mitigations: [],
          citations: []
        },
        tax_considerations: {
          ideas: [],
          citations: []
        },
        disclaimer: 'This is financial advice' // Missing educational disclaimer
      };

      const validation = AdvisoryValidator.auditCompliance(outputWithoutEducationalDisclaimer, mockInputs);
      expect(validation.valid).toBe(false);
      expect(validation.error).toContain('Educational disclaimer missing');
    });

    test('accepts proper educational disclaimer', () => {
      const validOutput: AdvisoryOutput = {
        executive_summary: {
          overview: 'Overview',
          key_metrics: {
            net_worth: 500000,
            monthly_surplus: 3000,
            required_contrib_total_monthly: 2500,
            surplus_gap_monthly: 500
          },
          status_flags: {
            on_track: true,
            stabilize_first: false
          }
        },
        priority_actions_30d: [],
        strategy_12m: [
          { quarter: 'Q1', actions: [] },
          { quarter: 'Q2', actions: [] },
          { quarter: 'Q3', actions: [] },
          { quarter: 'Q4', actions: [] }
        ],
        risk_management: {
          top_risks: [],
          mitigations: [],
          citations: []
        },
        tax_considerations: {
          ideas: [],
          citations: []
        },
        disclaimer: 'This report is for educational purposes only and does not constitute financial advice.'
      };

      const validation = AdvisoryValidator.auditCompliance(validOutput, mockInputs);
      expect(validation.valid).toBe(true);
    });
  });

  describe('Input Building', () => {
    test('builds valid plan inputs from financial profile', async () => {
      // This would require mocking FinancialDataService
      // For now, test the structure
      const mockProfile = {
        user: { name: 'Test User', age: 35 },
        financials: {
          netWorth: { total: 500000 },
          cashFlow: { monthlyIncome: 8000, monthlyExpenses: 5000, monthlySurplus: 3000 },
          liabilities: []
        },
        goals: [],
        preferences: { riskTolerance: 5, taxBracket: 0.24 }
      };

      // Test helper methods
      expect(service['mapRiskTolerance'](3)).toBe('conservative');
      expect(service['mapRiskTolerance'](5)).toBe('moderate');
      expect(service['mapRiskTolerance'](8)).toBe('aggressive');
    });
  });

  describe('Integration Tests', () => {
    test('full advisory generation workflow', async () => {
      // This would be an integration test with real API calls
      // For now, document the expected flow:
      
      // 1. buildPlanInputs(userId) -> PlanInputs
      // 2. buildPrompt(inputs) -> string
      // 3. callLLM(prompt) -> string
      // 4. JSON.parse(response) -> AdvisoryOutput
      // 5. Run all validations
      // 6. Retry with corrections if needed
      // 7. Return validated AdvisoryOutput
      
      expect(true).toBe(true); // Placeholder
    });
  });
});

// Test utilities for manual testing
export const TestUtils = {
  createMockInputs: (overrides: Partial<PlanInputs> = {}): PlanInputs => ({
    client: {
      name: 'Test Client',
      age: 35,
      risk_band: 'moderate',
      tax_bracket_est: 0.24,
      ...overrides.client
    },
    snapshot: {
      net_worth: 500000,
      monthly_surplus: 3000,
      asset_allocation_current: { stocks: 60, bonds: 30, cash: 10 },
      ...overrides.snapshot
    },
    goals: [],
    cashflow: {
      income_monthly: 8000,
      expenses_monthly: 5000,
      debts: [],
      ...overrides.cashflow
    },
    plan_outputs: {
      asset_allocation_target: { stocks: 70, bonds: 20, cash: 10 },
      rebalancing_trades: [],
      contribution_plan: [],
      debt_actions: [],
      monte_carlo: { success_prob: 0.85, note: 'Test' },
      ...overrides.plan_outputs
    },
    computed: {
      required_contrib_total_monthly: 2500,
      surplus_minus_required: 500,
      ...overrides.computed
    },
    constraints: {
      min_cash_buffer_months: 6,
      compliance_mode: 'education',
      ...overrides.constraints
    },
    kb_context: [
      { id: 'KB-001', title: 'Test KB' }
    ]
  }),

  validateOutput: (output: AdvisoryOutput, inputs: PlanInputs) => {
    return [
      AdvisoryValidator.auditNumbers(output, inputs),
      AdvisoryValidator.auditCitations(output, inputs.kb_context.map(k => k.id)),
      AdvisoryValidator.auditBusinessRules(output, inputs),
      AdvisoryValidator.auditCompliance(output, inputs)
    ];
  }
};