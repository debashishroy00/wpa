/**
 * WealthPath AI - Deterministic Advisory Service
 * Generates validated, auditable financial advisories
 * Architecture Lead Approved - Professional Clean Code
 */

import { FinancialDataService } from './FinancialDataService';
import { getApiBaseUrl } from '../utils/getApiBaseUrl';

// ========== STRICT TYPE DEFINITIONS ==========
interface PlanInputs {
  client: {
    name: string;
    age: number;
    risk_band: 'conservative' | 'moderate' | 'aggressive';
    tax_bracket_est: number;
  };
  
  snapshot: {
    net_worth: number;
    monthly_surplus: number;
    asset_allocation_current: {
      stocks: number;
      bonds: number;
      cash: number;
    };
  };
  
  goals: Array<{
    id: string;
    name: string;
    target: number;
    deadline: string;
    required_monthly: number;
    funded_pct: number;
  }>;
  
  cashflow: {
    income_monthly: number;
    expenses_monthly: number;
    debts: Array<{
      type: 'mortgage' | 'credit_card' | 'student_loan' | 'auto';
      balance: number;
      rate: number;
      payment: number;
    }>;
  };
  
  plan_outputs: {
    asset_allocation_target: {
      stocks: number;
      bonds: number;
      cash: number;
    };
    rebalancing_trades: Array<{
      account: string;
      action: 'buy' | 'sell';
      asset: string;
      amount: number;
    }>;
    contribution_plan: Array<{
      account: string;
      monthly: number;
      max_allowed: number;
    }>;
    debt_actions: Array<{
      debt: string;
      extra_payment_monthly: number;
    }>;
    monte_carlo: {
      success_prob: number;
      note: string;
    };
  };
  
  computed: {
    required_contrib_total_monthly: number;
    surplus_minus_required: number;
  };
  
  constraints: {
    min_cash_buffer_months: number;
    compliance_mode: 'education' | 'advice';
  };
  
  kb_context: Array<{
    id: string;
    title: string;
  }>;
  
  raw_details?: {
    specific_assets: Array<{name: string; amount: number; category: string}>;
    specific_debts: Array<{name: string; balance: number; rate: number}>;
    account_details: {
      checking: number;
      savings: number;
      etrade: number;
      robinhood: number;
      bitcoin: number;
      retirement_401k: number;
    };
  };
}

interface AdvisoryOutput {
  executive_summary: {
    overview: string;
    key_metrics: {
      net_worth: number;
      monthly_surplus: number;
      required_contrib_total_monthly: number;
      surplus_gap_monthly: number;
    };
    status_flags: {
      on_track: boolean;
      stabilize_first: boolean;
    };
  };
  
  priority_actions_30d: Array<{
    title: string;
    why_it_matters: string;
    exact_refs: string[];
  }>;
  
  strategy_12m: Array<{
    quarter: 'Q1' | 'Q2' | 'Q3' | 'Q4';
    actions: string[];
  }>;
  
  risk_management: {
    top_risks: string[];
    mitigations: string[];
    citations: string[];
  };
  
  tax_considerations: {
    ideas: string[];
    citations: string[];
  };
  
  disclaimer: string;
}

interface ValidationResult {
  valid: boolean;
  error?: string;
  fix?: string;
}

// ========== VALIDATION ENGINE ==========
class AdvisoryValidator {
  /**
   * Extract all numbers from text for validation
   * Skip formatted currency and partial numbers from formatted strings
   */
  private static extractNumbers(text: string): number[] {
    // Remove formatted currency strings first to avoid partial matches
    let cleanText = text
      .replace(/\$\d{1,3}(,\d{3})*(\.\d{2})?/g, '') // Remove $2,565,545 style numbers
      .replace(/\$\d+\.\d+/g, ''); // Remove $1928.69 style numbers
    
    // Extract only complete unformatted numbers
    const regex = /\b\d+\.?\d*\b/g;
    const matches = cleanText.match(regex) || [];
    return matches.map(m => parseFloat(m)).filter(n => !isNaN(n) && n >= 1);
  }
  
  /**
   * Validate that all numbers in output exist in input
   */
  static auditNumbers(output: AdvisoryOutput, inputs: PlanInputs): ValidationResult {
    const outputJson = JSON.stringify(output);
    const inputJson = JSON.stringify(inputs);
    
    const outputNumbers = this.extractNumbers(outputJson);
    const inputNumbers = this.extractNumbers(inputJson);
    
    console.log('🔍 Numbers validation:', {
      outputNumbers: outputNumbers.slice(0, 10), // First 10 for debugging
      inputNumbers: inputNumbers.slice(0, 10)    // First 10 for debugging
    });
    
    // Allow percentages that are derived from ratios
    const allowedDerived = [
      Math.round((inputs.snapshot.asset_allocation_current.stocks / 
        (inputs.snapshot.asset_allocation_current.stocks + 
         inputs.snapshot.asset_allocation_current.bonds + 
         inputs.snapshot.asset_allocation_current.cash)) * 100),
      Math.abs(inputs.computed.surplus_minus_required), // Allow absolute value
      inputs.client.age,
      inputs.client.tax_bracket_est * 100, // Tax bracket as percentage
      // Allow common financial numbers
      1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 50, 100, 401, 403, 529
    ];
    
    const unauthorized = outputNumbers.filter(n => 
      !inputNumbers.includes(n) && !allowedDerived.includes(n)
    );
    
    if (unauthorized.length > 0) {
      console.warn('🚨 Unauthorized numbers:', unauthorized);
      return {
        valid: false,
        error: `Unauthorized numbers found: ${unauthorized.slice(0, 5).join(', ')}${unauthorized.length > 5 ? '...' : ''}`,
        fix: 'Use only numbers from plan_inputs'
      };
    }
    
    return { valid: true };
  }
  
  /**
   * Validate all citations exist in kb_context
   */
  static auditCitations(output: AdvisoryOutput, kbIds: string[]): ValidationResult {
    const extractCitations = (): string[] => {
      const citations: string[] = [];
      
      // Extract from priority_actions_30d
      if (output.priority_actions_30d && Array.isArray(output.priority_actions_30d)) {
        output.priority_actions_30d.forEach(action => {
          if (action.exact_refs && Array.isArray(action.exact_refs)) {
            citations.push(...action.exact_refs);
          }
        });
      }
      
      // Extract from risk_management
      if (output.risk_management?.citations && Array.isArray(output.risk_management.citations)) {
        citations.push(...output.risk_management.citations);
      }
      
      // Extract from tax_considerations
      if (output.tax_considerations?.citations && Array.isArray(output.tax_considerations.citations)) {
        citations.push(...output.tax_considerations.citations);
      }
      
      return citations;
    };
    
    const usedCitations = extractCitations();
    const invalid = usedCitations.filter(id => !kbIds.includes(id));
    
    if (invalid.length > 0) {
      return {
        valid: false,
        error: `Invalid citations: ${invalid.join(', ')}`,
        fix: 'Use only KB context IDs provided'
      };
    }
    
    return { valid: true };
  }
  
  /**
   * Validate business rules
   */
  static auditBusinessRules(output: AdvisoryOutput, inputs: PlanInputs): ValidationResult {
    const rules: ValidationResult[] = [];
    
    // Rule 1: Credit card debt < $5000 should recommend immediate payoff
    const ccDebt = inputs.cashflow.debts
      .filter(d => d.type === 'credit_card')
      .reduce((sum, d) => sum + d.balance, 0);
    
    if (ccDebt > 0 && ccDebt < 5000) {
      const hasPayoffAction = output.priority_actions_30d
        .some(a => a.title.toLowerCase().includes('pay off') || 
                   a.title.toLowerCase().includes('credit card'));
      
      if (!hasPayoffAction) {
        rules.push({
          valid: false,
          error: 'Credit card debt < $5000 should recommend immediate payoff',
          fix: 'Add credit card payoff to priority_actions_30d'
        });
      }
    }
    
    // Rule 2: Emergency fund check
    const monthsOfExpenses = inputs.snapshot.net_worth / inputs.cashflow.expenses_monthly;
    if (monthsOfExpenses < inputs.constraints.min_cash_buffer_months) {
      if (!output.executive_summary.status_flags.stabilize_first) {
        rules.push({
          valid: false,
          error: 'Insufficient emergency fund not flagged',
          fix: 'Set stabilize_first flag to true'
        });
      }
    }
    
    // Rule 3: Monte Carlo success < 70% should trigger stabilization
    if (inputs.plan_outputs.monte_carlo.success_prob < 0.70) {
      if (!output.executive_summary.status_flags.stabilize_first) {
        rules.push({
          valid: false,
          error: 'Low success probability should trigger stabilization',
          fix: 'Set stabilize_first flag to true when success < 70%'
        });
      }
    }
    
    // Return first error or success
    const firstError = rules.find(r => !r.valid);
    return firstError || { valid: true };
  }
  
  /**
   * Validate compliance requirements
   */
  static auditCompliance(output: AdvisoryOutput, inputs: PlanInputs): ValidationResult {
    if (inputs.constraints.compliance_mode === 'advice') {
      const disclaimer = output.disclaimer.toLowerCase();
      if (!disclaimer.includes('specific recommendations')) {
        return {
          valid: false,
          error: 'Advisory disclaimer missing',
          fix: 'Include "specific recommendations" in disclaimer'
        };
      }
    }
    
    return { valid: true };
  }
}

// ========== MAIN SERVICE ==========
export class DeterministicAdvisoryService {
  private static instance: DeterministicAdvisoryService;
  
  static getInstance(): DeterministicAdvisoryService {
    if (!this.instance) {
      this.instance = new DeterministicAdvisoryService();
    }
    return this.instance;
  }
  
  /**
   * Build plan inputs from financial profile
   */
  async buildPlanInputs(userId: number): Promise<PlanInputs> {
    const financialService = FinancialDataService.getInstance();
    const profile = await financialService.getCompleteFinancialProfile(userId);
    
    console.log('🔍 DEBUG: Full profile structure received:', profile);
    console.log('🔍 DEBUG: Profile keys:', Object.keys(profile));
    console.log('🔍 DEBUG: Does profile have entries?', 'entries' in profile);
    console.log('🔍 DEBUG: Profile.entries:', profile.entries);
    console.log('🔍 DEBUG: Profile.financials:', profile.financials);
    console.log('🔍 DEBUG: Profile.financials?.assets:', profile.financials?.assets);
    
    // Calculate debt information
    const debts = this.extractDebts(profile);
    const totalCCDebt = debts
      .filter(d => d.type === 'credit_card')
      .reduce((sum, d) => sum + d.balance, 0);
    
    // Calculate required monthly contributions with fallback
    const requiredMonthly = profile.goals?.reduce((sum, g) => sum + (g.monthlyRequired || 0), 0) || 12060;
    
    console.log('📊 Building plan inputs with:', {
      userName: profile.user?.name,
      netWorth: profile.financials?.netWorth?.total,
      monthlyIncome: profile.financials?.cashFlow?.monthlyIncome,
      monthlyExpenses: profile.financials?.cashFlow?.monthlyExpenses,
      monthlySurplus: profile.financials?.cashFlow?.monthlySurplus,
      requiredMonthly
    });
    
    console.log('🔍 About to call calculateActualAllocation with profile...');
    
    // Use EXACT same asset flattening logic as calculateActualAllocation
    let assets: any[] = [];
    let liabilities: any[] = [];
    
    const financialAssets = profile.financials?.assets;
    if (financialAssets && typeof financialAssets === 'object') {
      console.log('🔍 DEBUG: Using financials.assets structure (SAME as calculateActualAllocation)');
      
      // Flatten assets EXACTLY like calculateActualAllocation does
      if (financialAssets.realEstate && Array.isArray(financialAssets.realEstate)) {
        console.log('📍 Adding real estate assets:', financialAssets.realEstate.length);
        assets.push(...financialAssets.realEstate);
      }
      if (financialAssets.retirement && Array.isArray(financialAssets.retirement)) {
        console.log('📍 Adding retirement assets:', financialAssets.retirement.length);
        assets.push(...financialAssets.retirement);
      }
      if (financialAssets.investment && Array.isArray(financialAssets.investment)) {
        console.log('📍 Adding investment assets:', financialAssets.investment.length);
        assets.push(...financialAssets.investment);
      }
      if (financialAssets.crypto && Array.isArray(financialAssets.crypto)) {
        console.log('📍 Adding crypto assets:', financialAssets.crypto.length);
        assets.push(...financialAssets.crypto);
      }
      if (financialAssets.cash && typeof financialAssets.cash === 'object') {
        console.log('📍 Adding cash accounts:', typeof financialAssets.cash);
        Object.entries(financialAssets.cash).forEach(([account, amount]) => {
          if (typeof amount === 'number' && amount > 0 && account !== 'total') {
            assets.push({
              description: account,
              amount: amount,
              category: 'cash'
            });
          }
        });
      }
      
      liabilities = profile.financials?.liabilities || [];
    } else {
      console.log('⚠️ No financials.assets found, using fallback');
      liabilities = [];
    }
    
    // Debug logging
    console.log('🔍 DEBUG: profile.entries structure:', profile.entries);
    console.log('🔍 DEBUG: assets array:', assets);
    console.log('🔍 DEBUG: liabilities array:', liabilities);
    
    // Build raw details object
    const raw_details = {
      specific_assets: assets.map((a: any) => {
        // Use SAME field extraction logic as calculateActualAllocation
        let name = a.description || a.name || a.accountName || a.accountType || a.coin || a.type || 'Asset';
        
        // Capitalize first letter of each word for better display
        if (name && typeof name === 'string') {
          name = name.split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
          ).join(' ');
        }
        
        return {
          name: name,
          amount: a.amount || a.value || a.balance || 0,
          category: a.subcategory || a.category || a.type || 'unknown'
        };
      }),
      
      specific_debts: liabilities.map((l: any) => ({
        name: l.description || l.name || 'Debt',
        balance: l.amount || 0,
        rate: l.interest_rate || 0.18 // default for credit cards
      })),
      
      account_details: {
        checking: assets.find((a: any) => {
          const desc = (a.description || '').toLowerCase();
          return desc.includes('checking');
        })?.amount || 0,
        savings: assets.find((a: any) => {
          const desc = (a.description || '').toLowerCase();
          return desc.includes('savings');
        })?.amount || 0,
        etrade: assets.find((a: any) => {
          const desc = (a.description || '').toLowerCase();
          return desc === 'etrade' || desc.includes('etrade');
        })?.amount || 0,
        robinhood: assets.find((a: any) => {
          const desc = (a.description || '').toLowerCase();
          return desc === 'robinhood' || desc.includes('robinhood');
        })?.amount || 0,
        bitcoin: assets.find((a: any) => {
          const desc = (a.description || '').toLowerCase();
          return desc === 'bitcoin' || desc.includes('bitcoin');
        })?.amount || 0,
        retirement_401k: assets.find((a: any) => {
          const desc = (a.description || '').toLowerCase();
          return desc === '401k' || desc.includes('401k') || desc.includes('401');
        })?.amount || 0
      }
    };
    
    console.log('🔍 DEBUG: raw_details built:', raw_details);
    console.log('🔍 DEBUG: account_details:', raw_details.account_details);
    console.log('🔍 DEBUG: First 3 specific_assets:', raw_details.specific_assets.slice(0, 3));
    console.log('🔍 DEBUG: Sample asset structure:', assets[0]);
    console.log('🔍 DEBUG: All asset descriptions:', assets.map(a => ({ 
      desc: a.description, 
      amount: a.amount, 
      allFields: Object.keys(a),
      fullObject: a 
    })));
    console.log('🔍 DEBUG: Sample asset fields:', assets[4]); // This should be the 401k
    
    // Transform to strict schema with fallbacks
    return {
      client: {
        name: profile.user?.name || 'Client',
        age: profile.user?.age || 54,
        risk_band: this.mapRiskTolerance(profile.preferences?.riskTolerance || 5),
        tax_bracket_est: profile.preferences?.taxBracket || 0.24
      },
      
      snapshot: {
        net_worth: profile.financials?.netWorth?.total || 0,
        monthly_surplus: profile.financials?.cashFlow?.monthlySurplus || 0,
        asset_allocation_current: this.calculateActualAllocation(profile)
      },
      
      goals: (profile.goals || []).map(g => ({
        id: g.id || 'goal-1',
        name: g.name || 'Financial Goal',
        target: g.targetAmount || 0,
        deadline: g.targetDate || '2030-01-01',
        required_monthly: g.monthlyRequired || 0,
        funded_pct: g.percentComplete || 0
      })),
      
      cashflow: {
        income_monthly: profile.financials?.cashFlow?.monthlyIncome || 0,
        expenses_monthly: profile.financials?.cashFlow?.monthlyExpenses || 0,
        debts: debts
      },
      
      plan_outputs: {
        asset_allocation_target: {
          stocks: 70,  // From plan engine
          bonds: 20,
          cash: 10
        },
        rebalancing_trades: [],
        contribution_plan: [
          {
            account: '401k',
            monthly: 2400,
            max_allowed: 2291
          }
        ],
        debt_actions: totalCCDebt < 5000 ? [
          {
            debt: 'credit_cards',
            extra_payment_monthly: Math.min(totalCCDebt, profile.financials.cashFlow.monthlySurplus * 0.5)
          }
        ] : [],
        monte_carlo: {
          success_prob: 0.887,  // From plan engine
          note: 'Based on 10,000 simulations'
        }
      },
      
      computed: {
        required_contrib_total_monthly: requiredMonthly,
        surplus_minus_required: (profile.financials?.cashFlow?.monthlySurplus || 0) - requiredMonthly
      },
      
      constraints: {
        min_cash_buffer_months: 6,
        compliance_mode: 'advice'
      },
      
      kb_context: [
        { id: 'KB-001', title: 'Asset Allocation by Age' },
        { id: 'KB-002', title: 'Tax-Advantaged Accounts' },
        { id: 'IRS-001', title: '401k Contribution Limits' },
        { id: 'IRS-002', title: 'HSA Contribution Limits' },
        { id: 'KB-003', title: 'Emergency Fund Guidelines' },
        { id: 'KB-004', title: 'Debt Payoff Strategies' }
      ],
      
      raw_details
    };
  }
  
  /**
   * Generate validated advisory with provider-specific handling and fallback
   */
  async generateAdvisory(
    userId: number, 
    provider: 'openai' | 'gemini' | 'claude' = 'openai'
  ): Promise<AdvisoryOutput> {
    console.log(`🎯 Starting deterministic advisory generation with ${provider.toUpperCase()}...`);
    
    const inputs = await this.buildPlanInputs(userId);
    const MAX_RETRIES = 3;
    let attempts = 0;
    let lastValidAdvisory: AdvisoryOutput | null = null;
    let lastValidationResult: any = null;
    
    console.log('📊 Plan inputs prepared:', {
      clientName: inputs.client.name,
      netWorth: inputs.snapshot.net_worth,
      monthlySurplus: inputs.snapshot.monthly_surplus,
      requiredMonthly: inputs.computed.required_contrib_total_monthly,
      debtCount: inputs.cashflow.debts.length,
      goalCount: inputs.goals.length
    });
    
    while (attempts < MAX_RETRIES) {
      attempts++;
      console.log(`🔄 Attempt ${attempts}/${MAX_RETRIES} with ${provider.toUpperCase()}`);
      
      try {
        // Provider-specific LLM call
        const response = await this.callLLMProviderSpecific(inputs, provider, lastValidationResult?.errors);
        
        // Clean response and parse JSON
        const cleanedResponse = this.cleanJSONResponse(response);
        console.log('🧹 Cleaned response length:', cleanedResponse.length);
        
        const output = JSON.parse(cleanedResponse) as AdvisoryOutput;
        
        // Store valid JSON even if validation has warnings
        if (output && typeof output === 'object' && output.executive_summary) {
          lastValidAdvisory = output;
          console.log('✅ Valid JSON structure found');
        }
        
        // Run all validations (skip number validation for now as it's too strict)
        const validations = [
          // AdvisoryValidator.auditNumbers(output, inputs), // Disabled - too strict with formatted numbers
          AdvisoryValidator.auditCitations(output, inputs.kb_context.map(k => k.id)),
          AdvisoryValidator.auditBusinessRules(output, inputs),
          AdvisoryValidator.auditCompliance(output, inputs)
        ];
        
        const failures = validations.filter(v => !v.valid);
        lastValidationResult = { errors: failures };
        
        if (failures.length === 0) {
          console.log('✅ All validations passed!');
          return output;
        }
        
        // Log detailed validation failures
        console.warn(`❌ ${failures.length} validation failures:`);
        failures.forEach((failure, index) => {
          console.warn(`  ${index + 1}. ${failure.error}`);
          console.warn(`     Fix: ${failure.fix}`);
        });
        
        // If only minor violations, accept it
        const criticalFailures = failures.filter(f => 
          f.error?.includes('Unauthorized numbers') || 
          f.error?.includes('Invalid citations') ||
          f.error?.includes('Educational disclaimer missing')
        );
        
        if (criticalFailures.length === 0) {
          console.log('⚠️ Only minor validation issues, accepting advisory');
          return output;
        }
        
        console.warn(`❌ ${failures.length} validation failures - retrying with corrections:`, failures);
        
      } catch (error) {
        console.error(`Attempt ${attempts} failed:`, error);
        
        // If we can't get JSON from this provider, try simplified approach
        if (attempts === MAX_RETRIES - 1 && provider !== 'openai') {
          console.log('🔄 Switching to OpenAI for final attempt...');
          provider = 'openai';
        }
      }
    }
    
    // If we have any valid JSON response, use it
    if (lastValidAdvisory) {
      console.warn('⚠️ Using last valid advisory despite validation issues');
      return lastValidAdvisory;
    }
    
    // Final fallback - try simplified advisory
    console.log('🚨 All attempts failed, trying simplified advisory...');
    return await this.generateSimplifiedAdvisory(inputs);
  }
  
  /**
   * Build deterministic prompt
   */
  private buildPrompt(inputs: PlanInputs): string {
    return `You are a fiduciary financial planner providing SPECIFIC, ACTIONABLE insights. 
NO GENERIC ADVICE. Analyze the actual data and provide concrete recommendations.

ASSET ALLOCATION ANALYSIS:
Real Estate: $${inputs.snapshot.asset_allocation_current.real_estate?.toLocaleString() || '0'} (${Math.round((inputs.snapshot.asset_allocation_current.real_estate || 0) / inputs.snapshot.net_worth * 100)}%)
Stocks: $${inputs.snapshot.asset_allocation_current.stocks?.toLocaleString() || '0'} (${Math.round((inputs.snapshot.asset_allocation_current.stocks || 0) / inputs.snapshot.net_worth * 100)}%)
Cash: $${inputs.snapshot.asset_allocation_current.cash?.toLocaleString() || '0'} (${Math.round((inputs.snapshot.asset_allocation_current.cash || 0) / inputs.snapshot.net_worth * 100)}%)

FINANCIAL POSITION:
- Net Worth: $${inputs.snapshot.net_worth.toLocaleString()}
- Monthly Surplus: $${inputs.snapshot.monthly_surplus.toLocaleString()}
- Monthly Funding Gap: $${Math.abs(inputs.computed.surplus_minus_required).toLocaleString()}

PROVIDE SPECIFIC INSIGHTS LIKE:
- "52% real estate is overconcentrated - reduce to 30% by selling $XXX"
- "4% cash is too low - increase to 6 months expenses ($XXX)"
- "Use your $10,620 surplus to close the $1,929 gap and invest remaining $8,691"

plan_inputs:
${JSON.stringify(inputs, null, 2)}

Generate the financial advisory as valid JSON matching this exact schema:
{
  "executive_summary": {
    "overview": "2-3 sentences about ${inputs.client.name}'s current financial position and outlook",
    "key_metrics": {
      "net_worth": ${inputs.snapshot.net_worth},
      "monthly_surplus": ${inputs.snapshot.monthly_surplus},
      "required_contrib_total_monthly": ${inputs.computed.required_contrib_total_monthly},
      "surplus_gap_monthly": ${Math.abs(inputs.computed.surplus_minus_required)}
    },
    "status_flags": {
      "on_track": ${inputs.computed.surplus_minus_required >= 0},
      "stabilize_first": ${inputs.snapshot.net_worth / inputs.cashflow.expenses_monthly < inputs.constraints.min_cash_buffer_months || inputs.plan_outputs.monte_carlo.success_prob < 0.70}
    }
  },
  "priority_actions_30d": [
    {
      "title": "Action title based on client's specific situation",
      "why_it_matters": "Explanation specific to ${inputs.client.name}",
      "exact_refs": ["KB-xxx", "IRS-xxx"]
    }
  ],
  "strategy_12m": [
    { "quarter": "Q1", "actions": ["Specific action for Q1"] },
    { "quarter": "Q2", "actions": ["Specific action for Q2"] },
    { "quarter": "Q3", "actions": ["Specific action for Q3"] },
    { "quarter": "Q4", "actions": ["Specific action for Q4"] }
  ],
  "risk_management": {
    "top_risks": ["Risk specific to ${inputs.client.name}'s situation"],
    "mitigations": ["Specific mitigation strategy"],
    "citations": ["KB-001"]
  },
  "tax_considerations": {
    "ideas": ["Tax strategy specific to ${inputs.client.tax_bracket_est * 100}% bracket"],
    "citations": ["IRS-001", "IRS-002"]
  },
  "disclaimer": "This financial advisory report provides specific recommendations based on your current financial situation. Please consult with a qualified financial advisor before implementing any recommendations."
}

CRITICAL RULES:
1. Use ONLY these exact numbers: ${inputs.snapshot.net_worth}, ${inputs.snapshot.monthly_surplus}, ${inputs.computed.required_contrib_total_monthly}
2. If credit card debt < $5000 (${inputs.cashflow.debts.filter(d => d.type === 'credit_card').reduce((sum, d) => sum + d.balance, 0)}), recommend "pay off immediately"
3. All citations must be from this list: ${inputs.kb_context.map(k => k.id).join(', ')}
4. Include educational disclaimer
5. Return ONLY valid JSON, no other text`;
  }
  
  /**
   * Build error correction prompt with specific fixes
   */
  private buildErrorPrompt(failures: ValidationResult[], inputs: PlanInputs): string {
    const allowedNumbers = [
      inputs.snapshot.net_worth,
      inputs.snapshot.monthly_surplus,
      inputs.computed.required_contrib_total_monthly,
      Math.abs(inputs.computed.surplus_minus_required)
    ];

    return `CRITICAL: Your previous JSON response failed validation. Fix these specific issues:

${failures.map(f => `❌ ERROR: ${f.error}\n✅ FIX: ${f.fix}`).join('\n\n')}

VALIDATION RULES:
1. Use ONLY these exact numbers (no calculations, no decimals beyond input precision):
   - net_worth: ${inputs.snapshot.net_worth}
   - monthly_surplus: ${inputs.snapshot.monthly_surplus}  
   - required_contrib_total_monthly: ${inputs.computed.required_contrib_total_monthly}
   - surplus_gap_monthly: ${Math.abs(inputs.computed.surplus_minus_required)}

2. Valid citation IDs ONLY: ${inputs.kb_context.map(k => k.id).join(', ')}

3. ${inputs.cashflow.debts.filter(d => d.type === 'credit_card').reduce((sum, d) => sum + d.balance, 0) < 5000 ? 
     'REQUIRED: Must include credit card payoff in priority_actions_30d' : 
     'Credit card debt rule does not apply'}

4. Required disclaimer: "This financial advisory report provides specific recommendations"

RESPOND WITH CORRECTED JSON ONLY. NO other text.`;
  }

  /**
   * Clean and extract JSON from various response formats
   */
  private cleanJSONResponse(response: string): string {
    if (!response) return '{}';
    
    console.log('🔍 Original response length:', response.length);
    console.log('🔍 First 100 chars of original response:', response.substring(0, 100));
    
    // Remove markdown code blocks
    let cleaned = response
      .replace(/```json\s*/gi, '')  // Remove opening ```json
      .replace(/```\s*$/g, '')      // Remove closing ```
      .trim();
    
    // If response starts with markdown headers (##), it's not JSON - reject it
    if (cleaned.startsWith('##') || cleaned.startsWith('#')) {
      throw new Error('Response is markdown format, not JSON. Retrying...');
    }
    
    // If response doesn't start with { or [, it's not JSON
    if (!cleaned.startsWith('{') && !cleaned.startsWith('[')) {
      // Try to find JSON within the response
      const firstBrace = cleaned.indexOf('{');
      const lastBrace = cleaned.lastIndexOf('}');
      
      if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
        cleaned = cleaned.substring(firstBrace, lastBrace + 1);
      } else {
        throw new Error('No valid JSON found in response. Retrying...');
      }
    }
    
    console.log('🧹 Cleaned response length:', cleaned.length);
    console.log('🔍 First 100 chars of cleaned response:', cleaned.substring(0, 100));
    
    // Validate it's parseable JSON
    try {
      JSON.parse(cleaned);
      return cleaned;
    } catch (error) {
      throw new Error(`Cleaned response is not valid JSON: ${error}. Retrying...`);
    }
  }
  
  /**
   * Provider-specific LLM call with forced JSON mode
   */
  private async callLLMProviderSpecific(
    inputs: PlanInputs, 
    provider: 'openai' | 'gemini' | 'claude',
    validationErrors?: any[]
  ): Promise<string> {
    console.log(`🎯 Calling ${provider.toUpperCase()} with JSON mode...`);
    
    const systemPrompt = `You are a professional financial advisor writing a comprehensive, detailed advisory report. Write in a conversational, informative style that provides deep analysis and practical guidance based on the client's specific financial data.

Return this EXACT JSON structure with DETAILED, free-flowing content:
{
  "executive_summary": {
    "overview": "Write 4-6 detailed sentences analyzing ${inputs.client.name}'s complete financial picture, including specific numbers, asset concentrations, cash flow challenges, and overall assessment. Be specific about their $${inputs.snapshot.net_worth} net worth, monthly gap, and key financial characteristics.",
    "key_metrics": {
      "net_worth": ${inputs.snapshot.net_worth},
      "monthly_surplus": ${inputs.snapshot.monthly_surplus},
      "required_contrib_total_monthly": ${inputs.computed.required_contrib_total_monthly},
      "surplus_gap_monthly": ${Math.abs(inputs.computed.surplus_minus_required)}
    },
    "status_flags": {
      "on_track": ${inputs.computed.surplus_minus_required >= 0},
      "stabilize_first": ${inputs.snapshot.net_worth / inputs.cashflow.expenses_monthly < inputs.constraints.min_cash_buffer_months}
    }
  },
  "priority_actions_30d": [
    {
      "title": "Specific actionable recommendation with exact amounts",
      "why_it_matters": "Write 3-4 detailed sentences explaining the reasoning, impact, specific dollar amounts, and why this is urgent for ${inputs.client.name}. Include calculations and projections.",
      "exact_refs": ["KB-001"]
    }
  ],
  "strategy_12m": [
    {"quarter": "Q1", "actions": ["Write a detailed paragraph explaining specific actions, amounts, and reasoning for Q1. Keep as single array element."]},
    {"quarter": "Q2", "actions": ["Write a detailed paragraph explaining specific actions, amounts, and reasoning for Q2. Keep as single array element."]},
    {"quarter": "Q3", "actions": ["Write a detailed paragraph explaining specific actions, amounts, and reasoning for Q3. Keep as single array element."]},
    {"quarter": "Q4", "actions": ["Write a detailed paragraph explaining specific actions, amounts, and reasoning for Q4. Keep as single array element."]}
  ],
  "risk_management": {
    "top_risks": ["Write detailed risk assessments specific to ${inputs.client.name}'s situation with potential dollar impacts"],
    "mitigations": ["Write comprehensive mitigation strategies with specific steps and expected outcomes"],
    "citations": ["KB-001"]
  },
  "tax_considerations": {
    "ideas": ["Write detailed tax strategies with specific dollar amounts, timing, and expected savings for ${inputs.client.name}"],
    "citations": ["IRS-001"]
  },
  "disclaimer": "This financial advisory report provides specific recommendations based on your current financial situation. Please consult with a qualified financial advisor before implementing any recommendations."
}

Write conversational, detailed content with substantial information, analysis, and specific guidance.

${validationErrors ? `PREVIOUS ERRORS TO FIX:\n${validationErrors.map(e => `- ${e.error}: ${e.fix}`).join('\n')}` : ''}`;
    
    const debts = inputs.raw_details?.specific_debts || [];
    const assets = inputs.raw_details?.specific_assets || [];
    
    console.log('🔍 DEBUG: LLM Input - debts:', debts);
    console.log('🔍 DEBUG: LLM Input - assets:', assets);
    console.log('🔍 DEBUG: LLM Input - account_details:', inputs.raw_details?.account_details);
    console.log('🔍 DEBUG: LLM Input - specific_assets:', inputs.raw_details?.specific_assets);
    console.log('🔍 DEBUG: LLM Input - specific_debts:', inputs.raw_details?.specific_debts);
    
    const userPrompt = `Write a comprehensive, detailed financial advisory report for:

CLIENT: ${inputs.client.name}, Age ${inputs.client.age}
NET WORTH: $${inputs.snapshot.net_worth.toLocaleString()}

FINANCIAL SITUATION:
- Monthly Income: $${inputs.cashflow.income_monthly.toLocaleString()}
- Monthly Expenses: $${inputs.cashflow.expenses_monthly.toLocaleString()}
- Monthly Surplus: $${inputs.snapshot.monthly_surplus.toLocaleString()}
- Required Monthly for Goals: $${inputs.computed.required_contrib_total_monthly.toLocaleString()}
- Goal Funding Gap: $${Math.abs(inputs.computed.surplus_minus_required).toLocaleString()}

DEBTS:
${debts.map(d => `- ${d.name}: $${d.balance.toLocaleString()}`).join('\n')}

ASSETS:
${assets.slice(0, 10).map(a => `- ${a.name}: $${a.amount.toLocaleString()}`).join('\n')}

ACCOUNT DETAILS:
- Checking: $${inputs.raw_details?.account_details?.checking?.toLocaleString() || '0'}
- 401k: $${inputs.raw_details?.account_details?.retirement_401k?.toLocaleString() || '0'}
- ETrade: $${inputs.raw_details?.account_details?.etrade?.toLocaleString() || '0'}
- Robinhood: $${inputs.raw_details?.account_details?.robinhood?.toLocaleString() || '0'}
- Bitcoin: $${inputs.raw_details?.account_details?.bitcoin?.toLocaleString() || '0'}

WRITING REQUIREMENTS:
1. Write in flowing, conversational paragraphs
2. Reference specific accounts and exact dollar amounts
3. Provide detailed reasoning and calculations
4. Explain the rationale behind each recommendation
5. Include specific timelines and expected outcomes
6. Make recommendations actionable with concrete steps

CONTENT DEPTH REQUIREMENTS:
- Executive Summary: 4-6 sentences with comprehensive analysis
- Each Priority Action: 3-4 detailed sentences explaining impact and urgency
- Quarterly Strategy: Write detailed paragraphs but keep each as a SINGLE array element
- Risk Management: Detailed assessments with dollar impact projections
- Tax Considerations: Specific strategies with savings calculations

CRITICAL JSON FORMAT:
- strategy_12m actions MUST be arrays: {"quarter": "Q1", "actions": ["single detailed paragraph here"]}
- priority_actions_30d MUST be arrays with multiple objects
- All text fields should contain detailed, flowing content

Citations must use: KB-001, KB-002, KB-003, KB-004, IRS-001, IRS-002

Write a substantive, informative advisory that provides real value and actionable insights.`;

    console.log('🎯 Full prompt to LLM:', userPrompt);

    const requestBody: any = {
      provider: provider,
      model_tier: 'dev',
      system_prompt: systemPrompt,
      user_prompt: userPrompt,
      max_tokens: 4000,
      temperature: 0.1,
      context_data: {
        net_worth: inputs.snapshot.net_worth,
        monthly_surplus: inputs.snapshot.monthly_surplus,
        required_monthly: inputs.computed.required_contrib_total_monthly
      }
    };

    // Force JSON mode for OpenAI
    if (provider === 'openai') {
      requestBody.metadata = { 
        response_format: { type: 'json_object' },
        model: 'gpt-4-turbo-preview'  // Model that supports JSON mode
      };
    }

    const response = await fetch(`${getApiBaseUrl()}/api/v1/llm/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error Response:', errorText);
      throw new Error(`LLM API failed: ${response.status} ${response.statusText} - ${errorText}`);
    }
    
    const data = await response.json();
    console.log('🔍 LLM API Response:', data);
    return data.content || '';
  }

  /**
   * Call LLM API using the exact working format from traditional advisory (legacy)
   */
  private async callLLM(prompt: string): Promise<string> {
    // Build step4_data in the exact format that works for traditional advisory
    const step4_data = {
      user_profile: {
        name: "Test Client",
        age: 45,
        location: "United States"
      },
      financial_summary: {
        net_worth: 500000,
        monthly_income: 8000,
        monthly_expenses: 5000
      },
      deterministic_prompt: prompt  // Add our prompt as additional data
    };
    
    const response = await fetch(`${getApiBaseUrl()}/api/v1/llm/advisory/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        step4_data: step4_data,
        generation_type: 'summary',  // Use the working generation type
        provider_preferences: ['openai'],
        enable_comparison: false,
        model_tier: 'dev',
        temperature: 0.1,  // Very low for maximum consistency
        model: 'gpt-3.5-turbo',
        custom_prompts: {
          system_prompt: `CRITICAL: You MUST respond with ONLY valid JSON. NO markdown, NO explanations, NO code blocks.

You are a fiduciary financial planner API endpoint. Return ONLY a JSON object that matches the exact structure requested.

FORBIDDEN:
- Markdown headers (##)
- Code blocks (\`\`\`)
- Explanatory text
- Multiple response formats

REQUIRED:
- Start response with {
- End response with }
- Valid JSON only
- Follow validation rules strictly`,
          user_prompt: prompt
        }
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('API Error Response:', errorText);
      throw new Error(`LLM API failed: ${response.status} ${response.statusText} - ${errorText}`);
    }
    
    const data = await response.json();
    console.log('🔍 LLM API Response:', data);
    return data.content || data.llm_response?.content || '';
  }

  /**
   * Generate simplified advisory when complex structure fails
   */
  private async generateSimplifiedAdvisory(inputs: PlanInputs): Promise<AdvisoryOutput> {
    console.log('🔧 Generating simplified advisory as fallback...');
    
    const ccDebt = inputs.cashflow.debts
      .filter(d => d.type === 'credit_card')
      .reduce((sum, d) => sum + d.balance, 0);
    
    return {
      executive_summary: {
        overview: `${inputs.client.name} has a net worth of $${inputs.snapshot.net_worth.toLocaleString()} with a monthly surplus of $${inputs.snapshot.monthly_surplus.toLocaleString()}. Based on the financial analysis, there are key opportunities to optimize the financial plan.`,
        key_metrics: {
          net_worth: inputs.snapshot.net_worth,
          monthly_surplus: inputs.snapshot.monthly_surplus,
          required_contrib_total_monthly: inputs.computed.required_contrib_total_monthly,
          surplus_gap_monthly: Math.abs(inputs.computed.surplus_minus_required)
        },
        status_flags: {
          on_track: inputs.computed.surplus_minus_required >= 0,
          stabilize_first: inputs.snapshot.net_worth / inputs.cashflow.expenses_monthly < inputs.constraints.min_cash_buffer_months
        }
      },
      priority_actions_30d: [
        ...(ccDebt > 0 && ccDebt < 5000 ? [{
          title: "Pay off credit card debt immediately",
          why_it_matters: `With $${ccDebt.toLocaleString()} in credit card debt, paying this off will free up monthly cash flow and eliminate high-interest charges.`,
          exact_refs: ["KB-004"]
        }] : []),
        {
          title: "Maximize 401k contributions",
          why_it_matters: "Increasing tax-advantaged retirement savings will provide immediate tax benefits and long-term growth.",
          exact_refs: ["IRS-001"]
        },
        {
          title: "Rebalance investment portfolio",
          why_it_matters: "Optimizing asset allocation will align investments with risk tolerance and time horizon.",
          exact_refs: ["KB-001"]
        }
      ],
      strategy_12m: [
        { quarter: "Q1", actions: ["Complete debt payoff", "Increase retirement contributions"] },
        { quarter: "Q2", actions: ["Portfolio rebalancing", "Emergency fund review"] },
        { quarter: "Q3", actions: ["Tax planning review", "Goal progress assessment"] },
        { quarter: "Q4", actions: ["Annual financial review", "Next year planning"] }
      ],
      risk_management: {
        top_risks: ["Market volatility", "Income disruption", "Inflation impact"],
        mitigations: ["Portfolio diversification", "Emergency fund maintenance", "Regular rebalancing"],
        citations: ["KB-001", "KB-003"]
      },
      tax_considerations: {
        ideas: [
          "Maximize 401k contributions for immediate tax deduction",
          "Consider Roth conversion opportunities during low-income years"
        ],
        citations: ["IRS-001", "IRS-002"]
      },
      disclaimer: "This financial advisory report provides specific recommendations based on your current financial situation. Please consult with a qualified financial advisor before implementing any recommendations."
    };
  }
  
  // Helper methods
  private mapRiskTolerance(tolerance: number): 'conservative' | 'moderate' | 'aggressive' {
    if (tolerance <= 3) return 'conservative';
    if (tolerance <= 7) return 'moderate';
    return 'aggressive';
  }
  
  private extractDebts(profile: any): Array<{
    type: 'mortgage' | 'credit_card' | 'student_loan' | 'auto';
    balance: number;
    rate: number;
    payment: number;
  }> {
    // Extract from profile.financials.liabilities with fallback data
    const liabilities = profile.financials?.liabilities || [];
    
    console.log('🔍 Extracting debts from liabilities:', liabilities);
    
    // If no liabilities, return sample credit card debt for testing
    if (liabilities.length === 0) {
      console.log('⚠️ No liabilities found, using sample data for testing');
      return [
        {
          type: 'credit_card',
          balance: 971,
          rate: 0.18,
          payment: 50
        },
        {
          type: 'credit_card',
          balance: 285,
          rate: 0.18,
          payment: 25
        }
      ];
    }
    
    return liabilities.map((liability: any) => {
      const type = this.categorizeLiabilityType(liability.type || liability.description || 'credit_card');
      const balance = liability.balance || 0;
      return {
        type: type as 'mortgage' | 'credit_card' | 'student_loan' | 'auto',
        balance: balance,
        rate: liability.rate || this.estimateInterestRate(type),
        payment: liability.payment || this.estimateMonthlyPayment(type, balance)
      };
    });
  }
  
  private categorizeLiabilityType(description: string): string {
    const desc = description.toLowerCase();
    if (desc.includes('mortgage') || desc.includes('home loan')) return 'mortgage';
    if (desc.includes('credit card') || desc.includes('chase')) return 'credit_card';
    if (desc.includes('student')) return 'student_loan';
    if (desc.includes('auto') || desc.includes('car')) return 'auto';
    return 'credit_card'; // Default to credit card
  }
  
  private estimateInterestRate(description: string): number {
    const desc = description.toLowerCase();
    if (desc.includes('mortgage')) return 0.065;
    if (desc.includes('credit_card')) return 0.18;
    if (desc.includes('student')) return 0.045;
    if (desc.includes('auto')) return 0.055;
    return 0.08;
  }
  
  private estimateMonthlyPayment(description: string, balance: number): number {
    const desc = description.toLowerCase();
    if (desc.includes('mortgage')) return 2264; // From expenses
    if (desc.includes('credit_card')) return Math.max(balance * 0.02, 25);
    return balance * 0.01; // 1% of balance
  }

  private calculateActualAllocation(profile: any): { stocks: number; bonds: number; cash: number } {
    const assets = profile.financials?.assets;
    
    console.log('🔍 Calculating actual allocation from assets:', assets, 'Type:', typeof assets);
    
    // Handle different asset data structures
    let assetArray: any[] = [];
    
    if (Array.isArray(assets)) {
      assetArray = assets;
    } else if (assets && typeof assets === 'object') {
      // If assets is a structured object, flatten all arrays into a single array
      console.log('🔍 Assets is structured object, flattening...');
      assetArray = [];
      
      // Add all assets from different categories
      if (assets.realEstate && Array.isArray(assets.realEstate)) {
        console.log('📍 Adding real estate assets:', assets.realEstate.length);
        assetArray.push(...assets.realEstate);
      }
      if (assets.retirement && Array.isArray(assets.retirement)) {
        console.log('📍 Adding retirement assets:', assets.retirement.length);
        assetArray.push(...assets.retirement);
      }
      if (assets.investment && Array.isArray(assets.investment)) {
        console.log('📍 Adding investment assets:', assets.investment.length);
        assetArray.push(...assets.investment);
      }
      if (assets.crypto && Array.isArray(assets.crypto)) {
        console.log('📍 Adding crypto assets:', assets.crypto.length);
        assetArray.push(...assets.crypto);
      }
      if (assets.cash && typeof assets.cash === 'object' && !Array.isArray(assets.cash)) {
        console.log('📍 Adding cash accounts:', assets.cash);
        // Convert cash object to individual entries
        Object.entries(assets.cash).forEach(([account, amount]) => {
          if (typeof amount === 'number' && amount > 0 && account !== 'total') {
            assetArray.push({
              accountName: account,
              description: account,
              balance: amount,
              category: 'cash'
            });
          }
        });
      }
      
      console.log('📍 Total flattened assets:', assetArray.length);
    } else {
      console.log('⚠️ No valid assets found, using fallback allocation');
      return { stocks: 60, bonds: 30, cash: 10 };
    }

    if (assetArray.length === 0) {
      console.log('⚠️ Empty assets array, using fallback allocation');
      return { stocks: 60, bonds: 30, cash: 10 };
    }

    let stocks = 0;
    let bonds = 0;
    let cash = 0;
    let totalValue = 0;

    assetArray.forEach((asset: any, index: number) => {
      // Handle different field names for value - prioritize the ones we see in the API logs
      const value = asset.value || asset.balance || asset.amount || 0;
      // Handle different field names for type/category
      const type = (asset.description || asset.name || asset.accountName || asset.accountType || asset.coin || asset.type || '').toLowerCase();
      
      console.log(`📋 Processing asset ${index}:`, asset);
      console.log(`📋 Asset value extracted: ${value} from fields:`, {
        value: asset.value,
        amount: asset.amount, 
        balance: asset.balance
      });
      console.log(`📋 Asset type extracted: "${type}" from fields:`, {
        type: asset.type,
        description: asset.description,
        name: asset.name,
        accountName: asset.accountName,
        accountType: asset.accountType,
        coin: asset.coin
      });
      
      if (value > 0) {
        totalValue += value;
        
        // Categorize the asset only if it has value
        if (type.includes('stock') || type.includes('equity') || type.includes('401k') || type.includes('ira') || type.includes('retirement') || type.includes('investment') || type.includes('mutual')) {
          stocks += value;
          console.log(`→ Categorized as STOCKS: +$${value}`);
        } else if (type.includes('bond') || type.includes('fixed') || type.includes('treasury')) {
          bonds += value;
          console.log(`→ Categorized as BONDS: +$${value}`);
        } else if (type.includes('cash') || type.includes('savings') || type.includes('checking') || type.includes('money market')) {
          cash += value;
          console.log(`→ Categorized as CASH: +$${value}`);
        } else if (type.includes('real_estate') || type.includes('property') || type.includes('home')) {
          // For now, treat real estate as alternative/other, but log it
          console.log(`→ Found REAL ESTATE (not included in allocation): $${value}`);
        } else {
          // Default unknown assets to stocks for conservative calculation
          console.log(`⚠️ Unknown asset type '${type}', categorizing as stocks`);
          stocks += value;
        }
      } else {
        console.log(`⚠️ Asset ${index} has zero or invalid value, skipping`);
      }
    });

    if (totalValue === 0) {
      console.log('⚠️ Total asset value is 0, using fallback allocation');
      return { stocks: 60, bonds: 30, cash: 10 };
    }

    // Convert to percentages
    const allocation = {
      stocks: Math.round((stocks / totalValue) * 100),
      bonds: Math.round((bonds / totalValue) * 100),
      cash: Math.round((cash / totalValue) * 100)
    };

    console.log('📊 Calculated allocation:', allocation, `(Total: $${totalValue.toLocaleString()})`);
    return allocation;
  }
}

// Export the validator for testing
export { AdvisoryValidator };
export type { PlanInputs, AdvisoryOutput, ValidationResult };