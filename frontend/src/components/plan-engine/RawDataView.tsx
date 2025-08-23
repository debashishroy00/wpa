/**
 * Step 4: Raw Data View Component
 * Displays pure calculation results with no subjective language
 */
import React, { useState } from 'react';
import { Copy, Download, Clock, Calculator, TrendingUp, AlertCircle } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';

interface PlanOutput {
  gap_analysis: {
    target_amount: number;
    current_amount: number;
    gap: number;
    time_horizon_years: number;
    monte_carlo_success_rate: number;
    percentile_95_amount?: number;
    percentile_50_amount?: number;
    percentile_5_amount?: number;
  };
  target_allocation: {
    us_stocks: number;
    intl_stocks: number;
    bonds: number;
    reits: number;
    cash: number;
    commodities?: number;
    crypto?: number;
  };
  rebalancing_trades: Array<{
    action: 'buy' | 'sell';
    symbol: string;
    amount: number;
    account?: string;
    tax_impact?: number;
  }>;
  contribution_schedule: {
    retirement_401k_percent: number;
    retirement_401k_annual: number;
    roth_ira_annual: number;
    hsa_annual?: number;
    taxable_monthly: number;
    total_monthly: number;
    employer_match_annual?: number;
    tax_savings_annual?: number;
  };
  debt_schedule: Array<{
    debt: string;
    balance: number;
    rate: number;
    action: string;
    monthly_payment?: number;
    payoff_months?: number;
    total_interest?: number;
    refinance_rate?: number;
    refinance_savings?: number;
  }>;
  plan_metrics: {
    expected_return: number;
    expected_volatility: number;
    sharpe_ratio: number;
    required_savings_rate: number;
    stress_test_30pct_drop: number;
    stress_test_50pct_drop?: number;
    max_drawdown_expected: number;
    years_to_goal: number;
    inflation_assumption: number;
  };
  calculation_timestamp: string;
  calculation_version: string;
}

interface RawDataViewProps {
  planOutput: PlanOutput;
  className?: string;
}

const RawDataView: React.FC<RawDataViewProps> = ({ planOutput, className = '' }) => {
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['gap_analysis']));

  const handleCopySection = async (sectionKey: string, data: any) => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopiedSection(sectionKey);
      setTimeout(() => setCopiedSection(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleExportJSON = () => {
    const dataStr = JSON.stringify(planOutput, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `plan-calculations-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const formatNumber = (num: number, type: 'currency' | 'percentage' | 'decimal' = 'decimal'): string => {
    switch (type) {
      case 'currency':
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(num);
      case 'percentage':
        return `${(num * 100).toFixed(1)}%`;
      default:
        return num.toFixed(4);
    }
  };

  const renderDataSection = (title: string, data: any, sectionKey: string, icon: React.ReactNode) => {
    const isExpanded = expandedSections.has(sectionKey);
    
    return (
      <Card key={sectionKey} className="mb-4">
        <Card.Body>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {icon}
              <h3 className="text-lg font-semibold text-white">{title}</h3>
              <button
                onClick={() => toggleSection(sectionKey)}
                className="text-gray-400 hover:text-white text-sm"
              >
                {isExpanded ? '[ - ]' : '[ + ]'}
              </button>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCopySection(sectionKey, data)}
              className={copiedSection === sectionKey ? 'text-green-400' : ''}
            >
              <Copy className="w-4 h-4 mr-1" />
              {copiedSection === sectionKey ? 'Copied' : 'Copy'}
            </Button>
          </div>
          
          {isExpanded && (
            <div className="bg-gray-950 rounded-lg p-4 border border-gray-700">
              <pre className="text-sm text-gray-300 overflow-x-auto font-mono">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          )}
        </Card.Body>
      </Card>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Calculator className="w-6 h-6 text-blue-500" />
            Step 4: Deterministic Plan Engine Output
          </h2>
          <p className="text-gray-400 mt-1">Pure mathematical calculations with no subjective interpretations</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-400">
            <Clock className="w-4 h-4 inline mr-1" />
            {new Date(planOutput.calculation_timestamp).toLocaleString()}
          </div>
          <Button onClick={handleExportJSON} className="bg-blue-600 hover:bg-blue-700">
            <Download className="w-4 h-4 mr-2" />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Calculation Metadata */}
      <Card>
        <Card.Body>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">
                {formatNumber(planOutput.gap_analysis.monte_carlo_success_rate, 'percentage')}
              </div>
              <div className="text-sm text-gray-400">Monte Carlo Success Rate</div>
              <div className="text-xs text-gray-500">10,000 simulations</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                {formatNumber(planOutput.contribution_schedule.total_monthly, 'currency')}
              </div>
              <div className="text-sm text-gray-400">Required Monthly Savings</div>
              <div className="text-xs text-gray-500">Optimized contribution schedule</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">
                {planOutput.gap_analysis.time_horizon_years}
              </div>
              <div className="text-sm text-gray-400">Years to Goal</div>
              <div className="text-xs text-gray-500">Planning horizon</div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Warning Notice */}
      <Card className="border-yellow-600 bg-yellow-900/20">
        <Card.Body>
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5" />
            <div>
              <h4 className="text-yellow-400 font-medium">Raw Calculation Data</h4>
              <p className="text-yellow-200 text-sm mt-1">
                This view contains pure mathematical outputs from the deterministic plan engine. 
                Numbers are not recommendations - they are computational results based on your inputs and historical market data.
                For professional advisory interpretation, switch to Advisory Report view.
              </p>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Data Sections */}
      {renderDataSection(
        'Gap Analysis',
        planOutput.gap_analysis,
        'gap_analysis',
        <TrendingUp className="w-5 h-5 text-blue-500" />
      )}

      {renderDataSection(
        'Target Allocation',
        planOutput.target_allocation,
        'target_allocation',
        <Calculator className="w-5 h-5 text-green-500" />
      )}

      {renderDataSection(
        'Rebalancing Trades',
        planOutput.rebalancing_trades,
        'rebalancing_trades',
        <TrendingUp className="w-5 h-5 text-purple-500" />
      )}

      {renderDataSection(
        'Contribution Schedule',
        planOutput.contribution_schedule,
        'contribution_schedule',
        <Calculator className="w-5 h-5 text-orange-500" />
      )}

      {renderDataSection(
        'Debt Schedule',
        planOutput.debt_schedule,
        'debt_schedule',
        <AlertCircle className="w-5 h-5 text-red-500" />
      )}

      {renderDataSection(
        'Plan Metrics',
        planOutput.plan_metrics,
        'plan_metrics',
        <TrendingUp className="w-5 h-5 text-cyan-500" />
      )}

      {/* Footer */}
      <Card className="border-gray-700">
        <Card.Body>
          <div className="text-sm text-gray-400 space-y-2">
            <div><strong>Engine Version:</strong> {planOutput.calculation_version}</div>
            <div><strong>Calculation Time:</strong> {planOutput.calculation_timestamp}</div>
            <div><strong>Data Sources:</strong> Historical market returns (1928-2024), IRS contribution limits (2024)</div>
            <div><strong>Assumptions:</strong> Inflation {formatNumber(planOutput.plan_metrics.inflation_assumption, 'percentage')}, 
                 Expected Return {formatNumber(planOutput.plan_metrics.expected_return, 'percentage')}</div>
            <div className="text-xs text-gray-500 mt-3">
              ⚠️ Deterministic calculations only - no subjective interpretations included
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
};

export default RawDataView;