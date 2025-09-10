import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, Target, Calendar } from 'lucide-react';
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
    savingsRate: 0,
    totalGoals: 0
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
        apiClient.get<{net_worth: number}>(`/api/v1/financial/live-summary/${userId}`),
        apiClient.get<{monthly_income: number; savings_rate: number}>(`/api/v1/financial/cash-flow/${userId}`),
        apiClient.get<Array<any>>(`/api/v1/goals?user_id=${userId}`)
      ]);

      setDashboardStats({
        netWorth: liveSummary.net_worth || 0,
        monthlyIncome: cashFlow.monthly_income || 0,
        savingsRate: cashFlow.savings_rate || 0,
        totalGoals: goals.length || 0
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

  // Quick stats cards data
  const statsCards = [
    {
      title: 'Net Worth',
      value: dashboardStats.netWorth,
      format: 'currency',
      icon: DollarSign,
      color: 'from-green-400 to-green-600',
      textColor: 'text-green-600'
    },
    {
      title: 'Monthly Income',
      value: dashboardStats.monthlyIncome,
      format: 'currency',
      icon: TrendingUp,
      color: 'from-blue-400 to-blue-600',
      textColor: 'text-blue-600'
    },
    {
      title: 'Savings Rate',
      value: dashboardStats.savingsRate,
      format: 'percentage',
      icon: Calendar,
      color: 'from-purple-400 to-purple-600',
      textColor: 'text-purple-600'
    },
    {
      title: 'Active Goals',
      value: dashboardStats.totalGoals,
      format: 'number',
      icon: Target,
      color: 'from-orange-400 to-orange-600',
      textColor: 'text-orange-600'
    }
  ];

  const formatValue = (value: number, format: string) => {
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statsCards.map((card) => {
            const IconComponent = card.icon;
            return (
              <div
                key={card.title}
                className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-3 rounded-lg bg-gradient-to-r ${card.color}`}>
                    <IconComponent className="w-6 h-6 text-white" />
                  </div>
                </div>
                <div>
                  <p className="text-gray-300 text-sm mb-1">{card.title}</p>
                  <p className={`text-2xl font-bold ${card.textColor}`}>
                    {loading ? (
                      <span className="animate-pulse">Loading...</span>
                    ) : (
                      formatValue(card.value, card.format)
                    )}
                  </p>
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