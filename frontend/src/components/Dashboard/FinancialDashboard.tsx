import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, Target, Calendar, Flame, Percent, CreditCard, ShoppingBag, PieChart } from 'lucide-react';
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

      // Debug logging
      console.log('Dashboard Data Debug:', {
        liveSummary,
        cashFlow
      });

      // Calculate burn rate: (monthlyExpenses / monthlyIncome) * 100
      const burnRate = cashFlow.monthly_income > 0 ? (cashFlow.monthly_expenses / cashFlow.monthly_income) * 100 : 0;
      
      // Calculate DTI ratio using actual debt payments from expense breakdown
      let monthlyDebtPayments = 0;
      if (cashFlow.expense_breakdown) {
        // Housing typically includes mortgage payments
        monthlyDebtPayments += cashFlow.expense_breakdown.housing || 0;
        // Transportation often includes car payments
        monthlyDebtPayments += cashFlow.expense_breakdown.transportation || 0;
        // You might want to add other categories that represent debt payments
      }
      const dtiRatio = cashFlow.monthly_income > 0 ? (monthlyDebtPayments / cashFlow.monthly_income) * 100 : 0;

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
        }
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

    // Calculate percentages and ensure they add up to 100%
    const liquidPct = (liquid / total) * 100;
    const investedPct = (invested / total) * 100;
    const realEstatePct = (real_estate / total) * 100;
    const otherPct = (other / total) * 100;
    
    // Round percentages and adjust for rounding errors
    const roundedLiquid = Math.round(liquidPct * 10) / 10;
    const roundedInvested = Math.round(investedPct * 10) / 10;
    const roundedRealEstate = Math.round(realEstatePct * 10) / 10;
    const roundedOther = Math.round(otherPct * 10) / 10;
    
    // Ensure total is exactly 100% by adjusting the largest component
    const roundedTotal = roundedLiquid + roundedInvested + roundedRealEstate + roundedOther;
    let finalLiquid = roundedLiquid;
    let finalInvested = roundedInvested;
    let finalRealEstate = roundedRealEstate;
    let finalOther = roundedOther;
    
    if (Math.abs(roundedTotal - 100) > 0.1) {
      const adjustment = 100 - roundedTotal;
      // Apply adjustment to the largest percentage
      const max = Math.max(roundedLiquid, roundedInvested, roundedRealEstate, roundedOther);
      if (roundedLiquid === max) finalLiquid += adjustment;
      else if (roundedInvested === max) finalInvested += adjustment;
      else if (roundedRealEstate === max) finalRealEstate += adjustment;
      else finalOther += adjustment;
    }

    // Calculate cumulative percentages for positioning using corrected values
    const investedStart = finalLiquid;
    const realEstateStart = finalLiquid + finalInvested;
    const otherStart = finalLiquid + finalInvested + finalRealEstate;

    return (
      <div className="flex items-center gap-2">
        <div className="relative w-8 h-8">
          <svg className="w-8 h-8 -rotate-90" viewBox="0 0 32 32">
            {/* Liquid - Cyan */}
            {finalLiquid > 0 && (
              <circle
                cx="16"
                cy="16"
                r="15.5"
                fill="transparent"
                stroke="#67E8F9"
                strokeWidth="2"
                strokeDasharray={`${finalLiquid} ${100 - finalLiquid}`}
                strokeDashoffset="0"
              />
            )}
            {/* Invested - Green */}
            {finalInvested > 0 && (
              <circle
                cx="16"
                cy="16"
                r="15.5"
                fill="transparent"
                stroke="#86EFAC"
                strokeWidth="2"
                strokeDasharray={`${finalInvested} ${100 - finalInvested}`}
                strokeDashoffset={`-${investedStart}`}
              />
            )}
            {/* Real Estate - Yellow */}
            {finalRealEstate > 0 && (
              <circle
                cx="16"
                cy="16"
                r="15.5"
                fill="transparent"
                stroke="#FDE047"
                strokeWidth="2"
                strokeDasharray={`${finalRealEstate} ${100 - finalRealEstate}`}
                strokeDashoffset={`-${realEstateStart}`}
              />
            )}
            {/* Other - Pink */}
            {finalOther > 0 && (
              <circle
                cx="16"
                cy="16"
                r="15.5"
                fill="transparent"
                stroke="#F9A8D4"
                strokeWidth="2"
                strokeDasharray={`${finalOther} ${100 - finalOther}`}
                strokeDashoffset={`-${otherStart}`}
              />
            )}
          </svg>
        </div>
        <div className="text-[10px] space-y-0.5">
          {finalLiquid > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-cyan-300 rounded-full"></div>
              <span className="text-purple-200">Cash {finalLiquid.toFixed(0)}%</span>
            </div>
          )}
          {finalInvested > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-green-300 rounded-full"></div>
              <span className="text-purple-200">Inv {finalInvested.toFixed(0)}%</span>
            </div>
          )}
          {finalRealEstate > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-yellow-300 rounded-full"></div>
              <span className="text-purple-200">RE {finalRealEstate.toFixed(0)}%</span>
            </div>
          )}
          {finalOther > 0 && (
            <div className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 bg-pink-300 rounded-full"></div>
              <span className="text-purple-200">Other {finalOther.toFixed(0)}%</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Quick stats cards data - Updated to match Financial Data page gradient colors
  const statsCards = [
    {
      title: 'Burn Rate',
      value: dashboardStats.burnRate,
      format: 'percentage',
      icon: Flame,
      color: 'bg-gradient-to-r from-blue-900 to-blue-800',
      textColor: 'text-white',
      labelColor: 'text-blue-200',
      iconColor: 'text-blue-400',
      descColor: 'text-blue-300',
      description: 'Percentage of income spent monthly'
    },
    {
      title: 'Debt-to-Income',
      value: dashboardStats.dtiRatio,
      format: 'percentage',
      icon: CreditCard,
      color: 'bg-gradient-to-r from-green-900 to-green-800',
      textColor: 'text-white',
      labelColor: 'text-green-200',
      iconColor: 'text-green-400',
      descColor: 'text-green-300',
      description: 'Monthly debt payments vs income'
    },
    {
      title: 'Top Expense',
      value: dashboardStats.topExpenseAmount,
      categoryName: dashboardStats.topExpenseCategory,
      format: 'expense-category',
      icon: ShoppingBag,
      color: 'bg-gradient-to-r from-red-900 to-red-800',
      textColor: 'text-white',
      labelColor: 'text-red-200',
      iconColor: 'text-red-400',
      descColor: 'text-red-300',
      description: 'Highest monthly spending category'
    },
    {
      title: 'Asset Diversification',
      value: dashboardStats.assetDiversificationScore,
      format: 'pie-chart',
      icon: PieChart,
      color: 'bg-gradient-to-r from-purple-900 to-purple-800',
      textColor: 'text-white',
      labelColor: 'text-purple-200',
      iconColor: 'text-purple-400',
      descColor: 'text-purple-300',
      description: 'Asset allocation breakdown',
      assetBreakdown: dashboardStats.assetBreakdown
    },
    {
      title: 'Savings Rate',
      value: dashboardStats.savingsRate,
      format: 'percentage',
      icon: Percent,
      color: 'bg-gradient-to-r from-green-900 to-green-800',
      textColor: 'text-white',
      labelColor: 'text-green-200',
      iconColor: 'text-green-400',
      descColor: 'text-green-300',
      description: dashboardStats.savingsRate >= 20 
        ? 'Excellent savings rate! (Target: 20%+)'
        : dashboardStats.savingsRate >= 10
        ? 'Good savings rate (Target: 20%+)'
        : 'Percentage of income saved monthly'
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
      default:
        return value.toString();
    }
  };

  return (
    <div className="w-full">
      <div className="container mx-auto px-4 py-3">
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-white mb-1">Financial Dashboard</h1>
          <p className="text-gray-300 text-sm">Track your financial progress and take snapshots of your wealth over time</p>
        </div>

        {/* Quick Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-2 mb-4">
          {statsCards.map((card) => {
            return (
              <div
                key={card.title}
                className={`${card.color} rounded-lg p-3 shadow-lg`}
              >
                <div className="flex items-center justify-between mb-1">
                  <p className={`text-xs font-medium ${(card as any).labelColor}`}>{card.title}</p>
                  <card.icon className={`w-4 h-4 ${(card as any).iconColor}`} />
                </div>
                {card.format === 'pie-chart' ? (
                  <div className="mt-1">
                    {loading ? (
                      <span className="animate-pulse text-white text-sm">Loading...</span>
                    ) : (
                      renderPieChart((card as any).assetBreakdown)
                    )}
                  </div>
                ) : (
                  <>
                    <p className={`text-lg font-bold ${card.textColor} mb-1`}>
                      {loading ? (
                        <span className="animate-pulse">Loading...</span>
                      ) : (
                        formatValue(card.value, card.format, (card as any).categoryName)
                      )}
                    </p>
                    {card.format === 'expense-category' && card.value > 0 && !loading && (
                      <p className={`text-xs ${(card as any).descColor}`}>
                        {formatValue(card.value, 'currency')}
                      </p>
                    )}
                  </>
                )}
                <p className={`text-xs mt-1 ${(card as any).descColor} line-clamp-2`}>{card.description}</p>
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