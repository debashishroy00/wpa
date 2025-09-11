import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, Target, Calendar, Flame, Percent, CreditCard, ShoppingBag, PieChart, Clock } from 'lucide-react';
import SnapshotButton from '../SnapshotButton';
import SnapshotTimeline from '../SnapshotTimeline';
import { apiClient } from '../../utils/api-simple';

interface FinancialDashboardProps {
}

const FinancialDashboard: React.FC<FinancialDashboardProps> = () => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [loading, setLoading] = useState(true);
  const [dashboardStats, setDashboardStats] = useState({
    netWorth: 0,
    monthlyIncome: 0,
    monthlyExpenses: 0,
    totalLiabilities: 0,
    savingsRate: 0,
    totalGoals: 0,
    burnRate: 0,
    dtiRatio: 0,
    topExpenseCategory: '',
    topExpenseAmount: 0,
    assetDiversificationScore: 0,
    assetBreakdown: {
      liquid: 0,
      invested: 0,
      real_estate: 0,
      other: 0
    },
    yearsToRetirement: 0
  });

  // Fetch real financial data from API
  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Extract user ID from stored auth tokens
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      // Decode JWT to get user ID (JWT payload is base64 encoded)
      const tokenParts = token.split('.');
      const payload = JSON.parse(atob(tokenParts[1]));
      const userId = payload.sub; // 'sub' field contains user ID
      
      console.log('Using user ID:', userId);

      // Fetch financial data in parallel
      const [liveSummary, cashFlow, goals] = await Promise.all([
        apiClient.get<{
          net_worth: number; 
          total_liabilities: number; 
          asset_breakdown: {
            liquid: number;
            invested: number;
            real_estate: number;
            other: number;
          }
        }>(`/api/v1/financial/live-summary/${userId}`),
        apiClient.get<{monthly_income: number; monthly_expenses: number; savings_rate: number; expense_breakdown: Record<string, number>}>(`/api/v1/financial/cash-flow/${userId}`),
        apiClient.get<Array<any>>(`/api/v1/goals?user_id=${userId}`)
      ]);

      // Calculate burn rate: (monthlyExpenses / monthlyIncome) * 100
      const burnRate = cashFlow.monthly_income > 0 ? (cashFlow.monthly_expenses / cashFlow.monthly_income) * 100 : 0;
      
      // Calculate DTI ratio: Estimate monthly debt payments as 5% of total debt
      const estimatedMonthlyDebtPayments = (liveSummary.total_liabilities || 0) * 0.05;
      const dtiRatio = cashFlow.monthly_income > 0 ? (estimatedMonthlyDebtPayments / cashFlow.monthly_income) * 100 : 0;

      // Find top expense category
      let topExpenseCategory = '';
      let topExpenseAmount = 0;
      if (cashFlow.expense_breakdown) {
        const expenses = Object.entries(cashFlow.expense_breakdown);
        if (expenses.length > 0) {
          const [category, amount] = expenses.reduce((max, current) => 
            current[1] > max[1] ? current : max
          );
          topExpenseCategory = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          topExpenseAmount = amount;
        }
      }

      // Calculate Asset Diversification Score (0-100)
      let assetDiversificationScore = 0;
      if (liveSummary.asset_breakdown) {
        const { liquid, invested, real_estate, other } = liveSummary.asset_breakdown;
        const totalAssets = liquid + invested + real_estate + other;
        
        if (totalAssets > 0) {
          // Calculate percentages
          const liquidPct = liquid / totalAssets;
          const investedPct = invested / totalAssets;
          const realEstatePct = real_estate / totalAssets;
          const otherPct = other / totalAssets;
          
          // Ideal diversification target percentages
          const idealLiquid = 0.20; // 20% liquid for emergency fund
          const idealInvested = 0.60; // 60% invested for growth
          const idealRealEstate = 0.15; // 15% real estate
          const idealOther = 0.05; // 5% other
          
          // Calculate diversification score using inverse of variance from ideal
          const liquidScore = Math.max(0, 100 - Math.abs(liquidPct - idealLiquid) * 500);
          const investedScore = Math.max(0, 100 - Math.abs(investedPct - idealInvested) * 500);
          const realEstateScore = Math.max(0, 100 - Math.abs(realEstatePct - idealRealEstate) * 500);
          const otherScore = Math.max(0, 100 - Math.abs(otherPct - idealOther) * 500);
          
          // Weighted average score
          assetDiversificationScore = (liquidScore + investedScore + realEstateScore + otherScore) / 4;
        }
      }

      // Calculate Years to Retirement (estimate)
      // Simplified calculation based on 4% rule and current savings rate
      let yearsToRetirement = 0;
      if (cashFlow.monthly_income > 0 && cashFlow.monthly_expenses > 0) {
        const annualExpenses = cashFlow.monthly_expenses * 12;
        const retirementTarget = annualExpenses * 25; // 4% rule
        const currentAssets = liveSummary.net_worth > 0 ? liveSummary.net_worth : 0;
        const monthlyNetSavings = cashFlow.monthly_income - cashFlow.monthly_expenses;
        const annualNetSavings = monthlyNetSavings * 12;
        
        if (annualNetSavings > 0) {
          const remaining = Math.max(0, retirementTarget - currentAssets);
          yearsToRetirement = Math.ceil(remaining / annualNetSavings);
          // Cap at reasonable numbers
          yearsToRetirement = Math.min(yearsToRetirement, 50);
        } else {
          yearsToRetirement = 50; // If not saving, set to max
        }
      }

      setDashboardStats({
        netWorth: liveSummary.net_worth || 0,
        monthlyIncome: cashFlow.monthly_income || 0,
        monthlyExpenses: cashFlow.monthly_expenses || 0,
        totalLiabilities: liveSummary.total_liabilities || 0,
        savingsRate: cashFlow.savings_rate || 0,
        totalGoals: goals.length || 0,
        burnRate: burnRate,
        dtiRatio: dtiRatio,
        topExpenseCategory: topExpenseCategory,
        topExpenseAmount: topExpenseAmount,
        assetDiversificationScore: assetDiversificationScore,
        assetBreakdown: liveSummary.asset_breakdown || {
          liquid: 0,
          invested: 0,
          real_estate: 0,
          other: 0
        },
        yearsToRetirement: yearsToRetirement
      });
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      // Keep default values of 0 on error
    } finally {
      setLoading(false);
    }
  };

  const refreshTimeline = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  // Simple pie chart component for asset breakdown
  const renderPieChart = (assetBreakdown: any) => {
    if (!assetBreakdown) return null;

    const { liquid, invested, real_estate, other } = assetBreakdown;
    const total = liquid + invested + real_estate + other;

    if (total === 0) {
      return (
        <div className="w-12 h-12 rounded-full bg-gray-600 flex items-center justify-center">
          <span className="text-xs text-gray-400">No Data</span>
        </div>
      );
    }

    const liquidPct = (liquid / total) * 100;
    const investedPct = (invested / total) * 100;
    const realEstatePct = (real_estate / total) * 100;
    const otherPct = (other / total) * 100;

    // Calculate cumulative percentages for positioning
    const investedStart = liquidPct;
    const realEstateStart = liquidPct + investedPct;
    const otherStart = liquidPct + investedPct + realEstatePct;

    return (
      <div className="flex items-center gap-2">
        <div className="relative w-12 h-12">
          <svg className="w-12 h-12 -rotate-90" viewBox="0 0 32 32">
            {/* Liquid - Blue */}
            {liquidPct > 0 && (
              <circle
                cx="16"
                cy="16"
                r="15.5"
                fill="transparent"
                stroke="#3B82F6"
                strokeWidth="1"
                strokeDasharray={`${liquidPct} ${100 - liquidPct}`}
                strokeDashoffset="0"
              />
            )}
            {/* Invested - Green */}
            {investedPct > 0 && (
              <circle
                cx="16"
                cy="16"
                r="15.5"
                fill="transparent"
                stroke="#10B981"
                strokeWidth="1"
                strokeDasharray={`${investedPct} ${100 - investedPct}`}
                strokeDashoffset={`-${investedStart}`}
              />
            )}
            {/* Real Estate - Orange */}
            {realEstatePct > 0 && (
              <circle
                cx="16"
                cy="16"
                r="15.5"
                fill="transparent"
                stroke="#F59E0B"
                strokeWidth="1"
                strokeDasharray={`${realEstatePct} ${100 - realEstatePct}`}
                strokeDashoffset={`-${realEstateStart}`}
              />
            )}
            {/* Other - Purple */}
            {otherPct > 0 && (
              <circle
                cx="16"
                cy="16"
                r="15.5"
                fill="transparent"
                stroke="#8B5CF6"
                strokeWidth="1"
                strokeDasharray={`${otherPct} ${100 - otherPct}`}
                strokeDashoffset={`-${otherStart}`}
              />
            )}
          </svg>
        </div>
        <div className="text-[10px] space-y-0.5">
          {liquidPct > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
              <span className="text-gray-300">Cash {liquidPct.toFixed(0)}%</span>
            </div>
          )}
          {investedPct > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
              <span className="text-gray-300">Inv {investedPct.toFixed(0)}%</span>
            </div>
          )}
          {realEstatePct > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full"></div>
              <span className="text-gray-300">RE {realEstatePct.toFixed(0)}%</span>
            </div>
          )}
          {otherPct > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-purple-500 rounded-full"></div>
              <span className="text-gray-300">Other {otherPct.toFixed(0)}%</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Quick stats cards data - New financial insights
  const statsCards = [
    {
      title: 'Burn Rate',
      value: dashboardStats.burnRate,
      format: 'percentage',
      icon: Flame,
      color: 'from-red-400 to-red-600',
      textColor: 'text-red-600',
      description: 'Percentage of income spent monthly'
    },
    {
      title: 'Debt-to-Income',
      value: dashboardStats.dtiRatio,
      format: 'percentage',
      icon: CreditCard,
      color: 'from-yellow-400 to-yellow-600',
      textColor: 'text-yellow-600',
      description: 'Monthly debt payments vs income'
    },
    {
      title: 'Top Expense',
      value: dashboardStats.topExpenseAmount,
      categoryName: dashboardStats.topExpenseCategory,
      format: 'expense-category',
      icon: ShoppingBag,
      color: 'from-orange-400 to-orange-600',
      textColor: 'text-orange-600',
      description: 'Highest monthly spending category'
    },
    {
      title: 'Asset Diversification',
      value: dashboardStats.assetDiversificationScore,
      format: 'pie-chart',
      icon: PieChart,
      color: 'from-blue-400 to-blue-600',
      textColor: 'text-blue-600',
      description: 'Asset allocation breakdown',
      assetBreakdown: dashboardStats.assetBreakdown
    },
    {
      title: 'Years to Retirement',
      value: dashboardStats.yearsToRetirement,
      format: 'years',
      icon: Clock,
      color: 'from-purple-400 to-purple-600',
      textColor: 'text-purple-600',
      description: 'Estimated years until financial independence'
    }
  ];

  const formatValue = (value: number, format: string, categoryName?: string) => {
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'expense-category':
        return categoryName || 'None';
      case 'score':
        return `${Math.round(value)}/100`;
      case 'years':
        return value === 50 ? '50+' : `${Math.round(value)}`;
      default:
        return value.toString();
    }
  };

  return (
    <div className="w-full">
      <div className="container mx-auto px-4 py-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Financial Dashboard</h1>
          <p className="text-gray-300">Track your financial progress and take snapshots of your wealth over time</p>
        </div>

        {/* Quick Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
          {statsCards.map((card) => {
            return (
              <div
                key={card.title}
                className="bg-white/10 backdrop-blur-lg rounded-lg p-3 border border-white/20"
              >
                <div>
                  <p className="text-gray-300 text-xs mb-2">{card.title}</p>
                  {card.format === 'pie-chart' ? (
                    <div className="mt-2">
                      {loading ? (
                        <span className="animate-pulse text-gray-400">Loading...</span>
                      ) : (
                        renderPieChart((card as any).assetBreakdown)
                      )}
                    </div>
                  ) : (
                    <>
                      <p className={`text-xl font-bold ${card.textColor}`}>
                        {loading ? (
                          <span className="animate-pulse">Loading...</span>
                        ) : (
                          formatValue(card.value, card.format, (card as any).categoryName)
                        )}
                      </p>
                      {card.format === 'expense-category' && card.value > 0 && !loading && (
                        <p className="text-gray-300 text-xs mt-1">
                          {formatValue(card.value, 'currency')}
                        </p>
                      )}
                    </>
                  )}
                  {card.description && (
                    <p className="text-gray-400 text-xs mt-1">{card.description}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Snapshot Section */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
            <div>
              <h2 className="text-xl font-semibold text-white mb-1">Historical Tracking</h2>
              <p className="text-gray-300 text-sm">Capture and track your financial state over time</p>
            </div>
            <SnapshotButton 
              onSnapshotCreated={refreshTimeline} 
              className="bg-blue-600 hover:bg-blue-700"
            />
          </div>
          <SnapshotTimeline refreshTrigger={refreshTrigger} />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <h3 className="text-white font-semibold mb-2">Update Profile</h3>
            <p className="text-gray-300 text-sm">Modify your personal information and preferences using the Profile tab above</p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <h3 className="text-white font-semibold mb-2">Add Financial Data</h3>
            <p className="text-gray-300 text-sm">Input your assets, liabilities, and income using the Financial Data tab above</p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
            <h3 className="text-white font-semibold mb-2">Chat with Advisor</h3>
            <p className="text-gray-300 text-sm">Get AI-powered financial advice and insights using the Chat tab above</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialDashboard;