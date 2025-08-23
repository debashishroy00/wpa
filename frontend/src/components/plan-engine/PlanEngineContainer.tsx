/**
 * Main Plan Engine Container Component
 * Orchestrates Step 4/5 view toggle and data management
 */
import React, { useState, useEffect } from 'react';
import { Calculator, FileText, RefreshCw, AlertTriangle } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import PlanEngineToggle, { ViewMode } from './PlanEngineToggle';
import RawDataView from './RawDataView';
import AdvisoryView from './AdvisoryView';
import { useAuthUser } from '../../stores/auth-store';
import { FinancialDataService } from '../../services/FinancialDataService';
import { apiClientFixed as apiClient } from '../../utils/api-fixed';

interface PlanEngineContainerProps {
  className?: string;
  onNext?: () => void;
}

const PlanEngineContainer: React.FC<PlanEngineContainerProps> = ({ 
  className = '', 
  onNext 
}) => {
  const user = useAuthUser();
  const [currentView, setCurrentView] = useState<ViewMode>('advisory_report');
  const [planOutput, setPlanOutput] = useState<any>(null);
  const [advisoryOutput, setAdvisoryOutput] = useState<any>(null);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load user preference from localStorage
  useEffect(() => {
    const savedView = localStorage.getItem('wealthpath_view_mode') as ViewMode;
    if (savedView && ['raw_data', 'advisory_report'].includes(savedView)) {
      setCurrentView(savedView);
    }
  }, []);

  // Save user preference to localStorage
  useEffect(() => {
    localStorage.setItem('wealthpath_view_mode', currentView);
  }, [currentView]);

  // Initial data load
  useEffect(() => {
    if (user?.id) {
      loadPlanData();
    }
  }, [user?.id]);

  const loadPlanData = async () => {
    try {
      setIsCalculating(true);
      setError(null);

      // Authentication guard
      if (!user?.id) {
        setError('User not authenticated');
        return;
      }

      // Step 1: Generate Step 4 calculations
      const planData = await apiClient.post('/api/v1/plan-engine/calculate', 
        await getUserFinancialData()
      );
      setPlanOutput(planData);

      // Step 2: Generate Step 5 advisory report
      const advisoryData = await apiClient.post('/api/v1/advisory/generate', {
        plan_input: await getUserFinancialData(),
        output_format: 'full'
      });
      setAdvisoryOutput(advisoryData);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      console.error('❌ Plan generation failed:', err);
    } finally {
      setIsCalculating(false);
    }
  };

  const getUserFinancialData = async () => {
    // Fetch user's actual financial data from the database
    if (!user?.id) {
      throw new Error('User not authenticated');
    }

    try {
      const financialService = FinancialDataService.getInstance();
      const userProfile = await financialService.getCompleteFinancialProfile(user.id);
      
      console.log('📊 User financial data loaded for plan engine:', {
        userId: user.id,
        netWorth: userProfile?.summary?.net_worth,
        hasAssets: !!userProfile?.assets,
        hasGoals: !!userProfile?.goals?.length
      });

      return userProfile;
    } catch (error) {
      console.error('❌ Failed to load user financial data:', error);
      throw error;
    }
  };

  const loadMockData = () => {
    // Mock Step 4 output
    setPlanOutput({
      gap_analysis: {
        target_amount: 2500000,
        current_amount: 485750,
        gap: 2014250,
        time_horizon_years: 17,
        monte_carlo_success_rate: 0.73,
        percentile_95_amount: 3200000,
        percentile_50_amount: 2650000,
        percentile_5_amount: 1850000
      },
      target_allocation: {
        us_stocks: 0.50,
        intl_stocks: 0.20,
        bonds: 0.20,
        reits: 0.05,
        cash: 0.05
      },
      rebalancing_trades: [
        { action: 'sell', symbol: 'VBTLX', amount: 31250, account: 'taxable' },
        { action: 'buy', symbol: 'VTI', amount: 23437, account: 'taxable' }
      ],
      contribution_schedule: {
        retirement_401k_percent: 0.18,
        retirement_401k_annual: 22500,
        roth_ira_annual: 7000,
        hsa_annual: 4150,
        taxable_monthly: 1850,
        total_monthly: 4375,
        employer_match_annual: 3750,
        tax_savings_annual: 6360
      },
      debt_schedule: [
        {
          debt: 'student_loans',
          balance: 35000,
          rate: 0.065,
          action: 'maintain_payment',
          monthly_payment: 385
        },
        {
          debt: 'mortgage',
          balance: 285000,
          rate: 0.065,
          action: 'refinance_to_5.8',
          refinance_rate: 0.058,
          refinance_savings: 115200
        }
      ],
      plan_metrics: {
        expected_return: 0.085,
        expected_volatility: 0.16,
        sharpe_ratio: 0.41,
        required_savings_rate: 0.31,
        stress_test_30pct_drop: 0.61,
        stress_test_50pct_drop: 0.45,
        max_drawdown_expected: 0.32,
        years_to_goal: 16.8,
        inflation_assumption: 0.03
      },
      calculation_timestamp: new Date().toISOString(),
      calculation_version: '1.0.0'
    });

    // Mock Step 5 output
    setAdvisoryOutput({
      executive_summary: [
        'Your portfolio has a 73% success rate with current strategy - a solid foundation with room for optimization [plan engine].',
        'Monthly savings requirement of $4,375 represents an aggressive but achievable 31% savings rate [plan engine].',
        'Mortgage refinancing from 6.5% to 5.8% could save $320/month and improve success rate by 2-3 percentage points [DP-001].'
      ],
      immediate_actions: [
        {
          text: 'Increase 401k contribution to 18% to capture full employer match - adds $200/month in free money [plan engine]',
          priority: 'high',
          category: 'retirement',
          timeline: '30_days'
        },
        {
          text: 'Begin mortgage refinancing process to reduce rate from 6.5% to 5.8% - potential $115,200 lifetime savings [DP-001]',
          priority: 'high',
          category: 'debt',
          timeline: '30_days'
        },
        {
          text: 'Rebalance portfolio to target allocation: increase US stocks to 50%, reduce bonds to 20% [RB-001]',
          priority: 'medium',
          category: 'investment',
          timeline: '30_days'
        }
      ],
      twelve_month_strategy: [
        {
          text: 'Implement systematic rebalancing quarterly to maintain target allocation and harvest tax losses [RB-001]',
          priority: 'medium',
          category: 'investment',
          timeline: 'quarterly'
        },
        {
          text: 'Optimize asset location by moving bonds to 401k and growth stocks to Roth IRA for tax efficiency [AL-001]',
          priority: 'medium',
          category: 'tax',
          timeline: 'annual'
        }
      ],
      risk_management: [
        {
          text: 'Portfolio stress test shows 61% success rate in 30% market decline - diversification across asset classes provides adequate protection [plan engine]',
          priority: 'medium',
          category: 'risk',
          timeline: 'ongoing'
        }
      ],
      tax_considerations: [
        {
          text: 'Current 24% tax bracket allows for $6,360 annual tax savings through optimized 401k and HSA contributions [IRS-001]',
          priority: 'medium',
          category: 'tax',
          timeline: 'annual'
        }
      ],
      citations: ['DP-001', 'RB-001', 'AL-001', 'IRS-001'],
      disclaimers: [
        'This analysis is for educational purposes only and not personalized financial advice.',
        'Investment returns are not guaranteed and past performance does not predict future results.',
        'Consider consulting with a qualified financial advisor for personalized recommendations.',
        'Tax implications may vary based on individual circumstances and current tax law.'
      ],
      plan_data_sources: ['plan_engine_v1.0.0', 'monte_carlo_simulation', 'target_allocation_optimizer'],
      generation_timestamp: new Date().toISOString()
    });
  };

  const handleViewChange = (newView: ViewMode) => {
    setCurrentView(newView);
  };

  const handleRefresh = () => {
    loadPlanData();
  };

  if (isCalculating) {
    return (
      <div className={`min-h-screen bg-gray-900 py-8 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4">
                <RefreshCw className="w-12 h-12 text-blue-600" />
              </div>
              <p className="text-gray-300 text-lg">Generating Financial Plan</p>
              <p className="text-sm text-gray-400 mt-2">
                Running Monte Carlo simulations and generating advisory recommendations...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !planOutput) {
    return (
      <div className={`min-h-screen bg-gray-900 py-8 ${className}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Card className="text-center py-8">
            <Card.Body>
              <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Plan Generation Failed</h3>
              <p className="text-gray-300 mb-6">{error}</p>
              <div className="flex gap-4 justify-center">
                <Button onClick={handleRefresh} className="bg-blue-600 hover:bg-blue-700">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </Button>
                <Button variant="outline" onClick={() => window.location.href = '/goals'}>
                  Check Setup
                </Button>
              </div>
            </Card.Body>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen bg-gray-900 py-8 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header with Toggle */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              {currentView === 'raw_data' ? (
                <Calculator className="w-8 h-8 text-blue-500" />
              ) : (
                <FileText className="w-8 h-8 text-green-500" />
              )}
              Financial Plan Analysis
            </h1>
            <p className="text-gray-300 mt-1">
              {currentView === 'raw_data' 
                ? 'Pure mathematical calculations with no subjective interpretations'
                : 'Professional advisory recommendations based on your plan calculations'
              }
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              onClick={handleRefresh}
              className="flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </Button>
            
            {onNext && (
              <Button
                onClick={onNext}
                className="bg-green-600 hover:bg-green-700"
              >
                Continue to Roadmap →
              </Button>
            )}
          </div>
        </div>

        {/* View Toggle */}
        <div className="mb-8">
          <PlanEngineToggle 
            currentView={currentView}
            onViewChange={handleViewChange}
            showViewIndicator={true}
          />
        </div>

        {/* Content Views */}
        {currentView === 'raw_data' && planOutput && (
          <RawDataView planOutput={planOutput} />
        )}

        {currentView === 'advisory_report' && advisoryOutput && planOutput && (
          <AdvisoryView 
            advisoryOutput={advisoryOutput}
            planOutput={planOutput}
          />
        )}

        {/* Action Buttons */}
        <div className="flex justify-center mt-12">
          {onNext && (
            <Button
              onClick={onNext}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 px-8"
            >
              Continue to Implementation Roadmap →
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlanEngineContainer;