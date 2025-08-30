import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import { 
  FileText, 
  DollarSign, 
  Calculator, 
  TrendingUp, 
  PieChart,
  AlertCircle,
  CheckCircle,
  BarChart3,
  Target,
  Percent
} from 'lucide-react';

interface TaxData {
  id?: number;
  tax_year: number;
  filing_status: string;
  adjusted_gross_income?: number;
  federal_tax_bracket?: number;
  state_tax_bracket?: number;
  // Enhanced fields
  state_tax_rate?: number;
  charitable_giving_annual?: number;
  tax_loss_harvesting_enabled?: boolean;
  backdoor_roth_eligible?: boolean;
  itemized_deduction_total?: number;
  mega_backdoor_roth_available?: boolean;
  business_income_details?: any;
  state_tax_deductions?: any;
  tax_planning_strategies?: any;
}

interface TaxInfo {
  tax_info: TaxData | null;
}

const EnhancedTaxManagement: React.FC = () => {
  const [taxData, setTaxData] = useState<TaxInfo>({ tax_info: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTaxOptimization, setShowTaxOptimization] = useState(false);
  const [showAdvancedStrategies, setShowAdvancedStrategies] = useState(false);
  const [showMultiYearAnalysis, setShowMultiYearAnalysis] = useState(false);
  
  const [taxFormData, setTaxFormData] = useState({
    adjusted_gross_income: '',
    filing_status: 'single',
    state_tax_rate: '',
    charitable_giving_annual: '',
    itemized_deduction_total: '',
    tax_loss_harvesting_enabled: false,
    backdoor_roth_eligible: false,
    mega_backdoor_roth_available: false
  });

  const [advancedStrategies, setAdvancedStrategies] = useState({
    backdoor_roth_conversion: '',
    mega_backdoor_roth_amount: '',
    tax_loss_harvesting_savings: '',
    charitable_bunching_strategy: false,
    business_income_amount: '',
    rental_income_amount: ''
  });

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  const getAuthToken = () => {
    return localStorage.getItem('access_token');
  };

  const apiCall = async (url: string, options: RequestInit = {}) => {
    const token = getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  };

  const loadTaxData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiCall('/api/v1/profile/complete-profile');
      setTaxData({ tax_info: response.tax_info || null });
      
      if (response.tax_info) {
        setTaxFormData({
          adjusted_gross_income: response.tax_info.adjusted_gross_income?.toString() || '',
          filing_status: response.tax_info.filing_status || 'single',
          state_tax_rate: response.tax_info.state_tax_rate?.toString() || '',
          charitable_giving_annual: response.tax_info.charitable_giving_annual?.toString() || '',
          itemized_deduction_total: response.tax_info.itemized_deduction_total?.toString() || '',
          tax_loss_harvesting_enabled: response.tax_info.tax_loss_harvesting_enabled || false,
          backdoor_roth_eligible: response.tax_info.backdoor_roth_eligible || false,
          mega_backdoor_roth_available: response.tax_info.mega_backdoor_roth_available || false
        });
      }
      
    } catch (err: any) {
      setError(err.message);
      console.error('Error loading tax data:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateFederalTaxBracket = (income: number, filingStatus: string) => {
    // 2024 tax brackets (simplified)
    const brackets2024 = {
      single: [
        { min: 0, max: 11600, rate: 10 },
        { min: 11600, max: 47150, rate: 12 },
        { min: 47150, max: 100525, rate: 22 },
        { min: 100525, max: 191650, rate: 24 },
        { min: 191650, max: 243725, rate: 32 },
        { min: 243725, max: 609350, rate: 35 },
        { min: 609350, max: Infinity, rate: 37 }
      ],
      married_filing_jointly: [
        { min: 0, max: 23200, rate: 10 },
        { min: 23200, max: 94300, rate: 12 },
        { min: 94300, max: 201050, rate: 22 },
        { min: 201050, max: 383900, rate: 24 },
        { min: 383900, max: 487450, rate: 32 },
        { min: 487450, max: 731200, rate: 35 },
        { min: 731200, max: Infinity, rate: 37 }
      ]
    };

    const applicableBrackets = brackets2024[filingStatus as keyof typeof brackets2024] || brackets2024.single;
    for (const bracket of applicableBrackets) {
      if (income > bracket.min && income <= bracket.max) {
        return bracket.rate;
      }
    }
    return 37; // Top bracket
  };

  const calculateTaxSavingsOpportunities = () => {
    const income = parseFloat(taxFormData.adjusted_gross_income) || 0;
    const charitableGiving = parseFloat(taxFormData.charitable_giving_annual) || 0;
    const stateRate = parseFloat(taxFormData.state_tax_rate) || 0;
    
    if (!income) return null;

    const federalBracket = calculateFederalTaxBracket(income, taxFormData.filing_status);
    const marginalRate = federalBracket + stateRate;
    
    // Calculate various tax savings opportunities
    const charitableTaxSavings = charitableGiving * (marginalRate / 100);
    const standardDeduction2024 = taxFormData.filing_status === 'married_filing_jointly' ? 29200 : 14600;
    const itemizedDeductions = parseFloat(taxFormData.itemized_deduction_total) || 0;
    const itemizingBenefit = Math.max(0, itemizedDeductions - standardDeduction2024) * (marginalRate / 100);

    // Backdoor Roth opportunity
    const backdoorRothSavings = income > 153000 ? 7000 * (marginalRate / 100) : 0; // 2024 IRA limit

    return {
      federalBracket,
      marginalRate,
      charitableTaxSavings,
      itemizingBenefit,
      backdoorRothSavings,
      taxLossHarvestingSavings: taxFormData.tax_loss_harvesting_enabled ? income * 0.005 : 0, // Estimated 0.5% of income
      totalPotentialSavings: charitableTaxSavings + itemizingBenefit + backdoorRothSavings
    };
  };

  const generateTaxPlanningRecommendations = () => {
    const income = parseFloat(taxFormData.adjusted_gross_income) || 0;
    const recommendations = [];

    if (income > 153000 && !taxFormData.backdoor_roth_eligible) {
      recommendations.push({
        strategy: 'Backdoor Roth IRA',
        description: 'You may be eligible for a backdoor Roth IRA conversion',
        potentialSavings: '$1,400+ annually in tax-free growth',
        priority: 'high'
      });
    }

    if (income > 230000 && taxFormData.mega_backdoor_roth_available) {
      recommendations.push({
        strategy: 'Mega Backdoor Roth',
        description: 'Maximize after-tax 401k contributions and convert to Roth',
        potentialSavings: 'Up to $46,000 additional tax-free savings',
        priority: 'high'
      });
    }

    if (parseFloat(taxFormData.charitable_giving_annual) > 5000) {
      recommendations.push({
        strategy: 'Charitable Bunching',
        description: 'Bundle multiple years of charitable giving into one year',
        potentialSavings: 'Maximize itemized deductions',
        priority: 'medium'
      });
    }

    if (!taxFormData.tax_loss_harvesting_enabled && income > 75000) {
      recommendations.push({
        strategy: 'Tax Loss Harvesting',
        description: 'Systematically realize investment losses to offset gains',
        potentialSavings: 'Up to $3,000 annually in tax savings',
        priority: 'medium'
      });
    }

    return recommendations;
  };

  useEffect(() => {
    loadTaxData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <Card className="bg-red-900/20 border-red-500/20 p-4">
          <div className="flex items-center space-x-2 text-red-400">
            <AlertCircle className="h-4 w-4" />
            <span>Error: {error}</span>
          </div>
        </Card>
      )}

      {/* Tax Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gray-800 border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Tax Bracket</p>
              <p className="text-white text-2xl font-bold">
                {taxFormData.adjusted_gross_income ? 
                  `${calculateFederalTaxBracket(parseFloat(taxFormData.adjusted_gross_income), taxFormData.filing_status)}%` : 
                  'N/A'}
              </p>
              <p className="text-white text-sm">Federal marginal rate</p>
            </div>
            <Percent className="h-8 w-8 text-red-400" />
          </div>
        </Card>

        <Card className="bg-gray-800 border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">AGI</p>
              <p className="text-white text-2xl font-bold">
                ${taxFormData.adjusted_gross_income ? 
                  parseFloat(taxFormData.adjusted_gross_income).toLocaleString() : 
                  '0'}
              </p>
              <p className="text-white text-sm">Adjusted Gross Income</p>
            </div>
            <DollarSign className="h-8 w-8 text-green-400" />
          </div>
        </Card>

        <Card className="bg-gray-800 border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Charitable</p>
              <p className="text-white text-2xl font-bold">
                ${taxFormData.charitable_giving_annual ? 
                  parseFloat(taxFormData.charitable_giving_annual).toLocaleString() : 
                  '0'}
              </p>
              <p className="text-white text-sm">Annual giving</p>
            </div>
            <Target className="h-8 w-8 text-blue-400" />
          </div>
        </Card>

        <Card className="bg-gray-800 border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Strategies</p>
              <p className="text-white text-2xl font-bold">
                {[
                  taxFormData.tax_loss_harvesting_enabled,
                  taxFormData.backdoor_roth_eligible,
                  taxFormData.mega_backdoor_roth_available
                ].filter(Boolean).length}
              </p>
              <p className="text-white text-sm">Active strategies</p>
            </div>
            <TrendingUp className="h-8 w-8 text-purple-400" />
          </div>
        </Card>
      </div>

      {/* Tax Optimization Form */}
      <Card className="bg-gray-800 border-gray-700">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Calculator className="h-5 w-5 text-blue-400" />
              <h3 className="text-white text-lg font-semibold">Tax Information & Optimization</h3>
            </div>
            <Button 
              onClick={() => setShowTaxOptimization(!showTaxOptimization)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {showTaxOptimization ? 'Hide' : 'Configure'}
            </Button>
          </div>

          {showTaxOptimization && (
            <div className="bg-gray-900 p-4 rounded-lg space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-white block mb-2">Adjusted Gross Income</label>
                  <Input
                    type="number"
                    placeholder="e.g. 150000"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={taxFormData.adjusted_gross_income}
                    onChange={(e) => setTaxFormData({...taxFormData, adjusted_gross_income: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-white block mb-2">Filing Status</label>
                  <select 
                    className="w-full p-2 bg-gray-800 border border-gray-600 text-white rounded"
                    value={taxFormData.filing_status}
                    onChange={(e) => setTaxFormData({...taxFormData, filing_status: e.target.value})}
                  >
                    <option value="single">Single</option>
                    <option value="married_filing_jointly">Married Filing Jointly</option>
                    <option value="married_filing_separately">Married Filing Separately</option>
                    <option value="head_of_household">Head of Household</option>
                  </select>
                </div>
                <div>
                  <label className="text-white block mb-2">State Tax Rate (%)</label>
                  <Input
                    type="number"
                    step="0.1"
                    placeholder="e.g. 7.5"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={taxFormData.state_tax_rate}
                    onChange={(e) => setTaxFormData({...taxFormData, state_tax_rate: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-white block mb-2">Annual Charitable Giving</label>
                  <Input
                    type="number"
                    placeholder="e.g. 15000"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={taxFormData.charitable_giving_annual}
                    onChange={(e) => setTaxFormData({...taxFormData, charitable_giving_annual: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-white block mb-2">Itemized Deductions Total</label>
                  <Input
                    type="number"
                    placeholder="e.g. 25000"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={taxFormData.itemized_deduction_total}
                    onChange={(e) => setTaxFormData({...taxFormData, itemized_deduction_total: e.target.value})}
                  />
                </div>
              </div>

              <div className="space-y-3">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={taxFormData.tax_loss_harvesting_enabled}
                    onChange={(e) => setTaxFormData({...taxFormData, tax_loss_harvesting_enabled: e.target.checked})}
                    className="text-blue-500"
                  />
                  <span className="text-white">Tax-loss harvesting enabled</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={taxFormData.backdoor_roth_eligible}
                    onChange={(e) => setTaxFormData({...taxFormData, backdoor_roth_eligible: e.target.checked})}
                    className="text-blue-500"
                  />
                  <span className="text-white">Backdoor Roth IRA eligible</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={taxFormData.mega_backdoor_roth_available}
                    onChange={(e) => setTaxFormData({...taxFormData, mega_backdoor_roth_available: e.target.checked})}
                    className="text-blue-500"
                  />
                  <span className="text-white">Mega backdoor Roth available</span>
                </label>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Tax Savings Analysis */}
      {taxFormData.adjusted_gross_income && (
        <Card className="bg-gray-800 border-gray-700">
          <div className="p-6">
            <div className="flex items-center space-x-2 mb-4">
              <BarChart3 className="h-5 w-5 text-green-400" />
              <h3 className="text-white text-lg font-semibold">Tax Savings Analysis</h3>
            </div>
            
            {(() => {
              const analysis = calculateTaxSavingsOpportunities();
              return analysis ? (
                <div>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Marginal Tax Rate</p>
                      <p className="text-white font-bold text-xl">{analysis.marginalRate.toFixed(1)}%</p>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Charitable Savings</p>
                      <p className="text-white font-bold text-xl">${analysis.charitableTaxSavings.toLocaleString()}</p>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Itemizing Benefit</p>
                      <p className="text-white font-bold text-xl">${analysis.itemizingBenefit.toLocaleString()}</p>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <p className="text-gray-400 text-sm">Total Savings</p>
                      <p className="text-white font-bold text-xl">${analysis.totalPotentialSavings.toLocaleString()}</p>
                    </div>
                  </div>
                </div>
              ) : null;
            })()}
          </div>
        </Card>
      )}

      {/* Tax Planning Recommendations */}
      {taxFormData.adjusted_gross_income && (
        <Card className="bg-gray-800 border-gray-700">
          <div className="p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Target className="h-5 w-5 text-yellow-400" />
              <h3 className="text-white text-lg font-semibold">Tax Planning Recommendations</h3>
            </div>
            
            <div className="space-y-4">
              {generateTaxPlanningRecommendations().map((rec, index) => (
                <div key={index} className={`p-4 rounded-lg border ${
                  rec.priority === 'high' ? 'bg-red-900/20 border-red-500/20' :
                  'bg-yellow-900/20 border-yellow-500/20'
                }`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-white font-medium">{rec.strategy}</h4>
                      <p className="text-gray-300 text-sm mt-1">{rec.description}</p>
                      <p className="text-gray-400 text-sm mt-1">Potential: {rec.potentialSavings}</p>
                    </div>
                    <div className={`px-2 py-1 rounded text-xs font-medium ${
                      rec.priority === 'high' ? 'bg-red-600 text-white' :
                      'bg-yellow-600 text-white'
                    }`}>
                      {rec.priority.toUpperCase()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4">
        <Button 
          onClick={loadTaxData}
          className="bg-gray-600 hover:bg-gray-700 text-white"
        >
          Refresh Data
        </Button>
      </div>
    </div>
  );
};

export default EnhancedTaxManagement;