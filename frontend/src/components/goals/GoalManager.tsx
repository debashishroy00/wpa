/**
 * WealthPath AI - Goal Manager Component
 * Main component for managing financial goals
 */
import React, { useState } from 'react';
import { 
  Target, 
  Plus, 
  TrendingUp, 
  Calendar, 
  AlertTriangle,
  Settings,
  Filter,
  Eye,
  Edit3,
  Trash2
} from 'lucide-react';

import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { 
  useGoalsQuery, 
  useGoalSummaryQuery,
  useDeleteGoalMutation,
  useUpdateGoalMutation
} from '../../hooks/use-goal-queries';
import { GOAL_CATEGORIES, GOAL_STATUSES } from '../../types/goals';
import type { Goal } from '../../types/goals';

import GoalForm from './GoalForm';
import GoalDetails from './GoalDetails';
import UserPreferencesForm from './UserPreferencesForm';

interface GoalManagerProps {
  className?: string;
}

const GoalManager: React.FC<GoalManagerProps> = ({ className = '' }) => {
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [showPreferences, setShowPreferences] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [viewMode, setViewMode] = useState<'list' | 'timeline'>('list');

  const { data: goals = [], isLoading, error, refetch } = useGoalsQuery({
    status: statusFilter || undefined,
    category: categoryFilter || undefined,
  });

  // Mutations
  const deleteGoalMutation = useDeleteGoalMutation();
  const updateGoalMutation = useUpdateGoalMutation();

  // Debug logging
  console.log('🎯 GoalManager render:', { 
    goals, 
    goalsLength: goals?.length, 
    isLoading, 
    error,
    statusFilter,
    categoryFilter,
    goalsType: typeof goals,
    goalsIsArray: Array.isArray(goals),
    firstGoal: goals?.[0]
  });
  
  // Additional debug check
  if (goals && !Array.isArray(goals)) {
    console.error('⚠️ Goals is not an array! Got:', goals);
  }

  const { data: summary } = useGoalSummaryQuery();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getDaysUntilTarget = (targetDate: string) => {
    const today = new Date();
    const target = new Date(targetDate);
    const diffTime = target.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-500';
    if (percentage >= 50) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getPriorityBadgeColor = (priority: number) => {
    if (priority >= 8) return 'bg-red-100 text-red-800 border border-red-300';
    if (priority >= 5) return 'bg-yellow-100 text-yellow-800 border border-yellow-300';
    return 'bg-green-100 text-green-800 border border-green-300';
  };

  const getPriorityLabel = (priority: number) => {
    if (priority >= 8) return 'Critical';
    if (priority >= 6) return 'High Priority';
    if (priority >= 4) return 'Medium Priority';
    return 'Low Priority';
  };

  const getCategoryEmoji = (category: string) => {
    const emojiMap: Record<string, string> = {
      'retirement': '🏖️',
      'real_estate': '🏠',
      'education': '🎓',
      'business': '🚀',
      'emergency_fund': '🛡️',
      'vacation': '🏝️',
      'vehicle': '🚗',
      'health': '💊',
      'custom': '💰'
    };
    return emojiMap[category] || '💰';
  };

  const getCashRequired = (goal: Goal) => {
    if (goal.category === 'real_estate' && goal.params?.down_payment_percentage) {
      const downPaymentPercent = goal.params.down_payment_percentage / 100;
      return goal.target_amount * downPaymentPercent;
    }
    return goal.target_amount;
  };

  const calculateMonthlySavingsRequired = (goal: Goal) => {
    const targetDate = new Date(goal.target_date);
    const today = new Date();
    const monthsRemaining = Math.max(1, Math.ceil((targetDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24 * 30)));
    
    let cashRequired = goal.target_amount;
    
    // For real estate goals, calculate based on down payment instead of full purchase price
    if (goal.category === 'real_estate' && goal.params?.down_payment_percentage) {
      const downPaymentPercent = goal.params.down_payment_percentage / 100;
      cashRequired = goal.target_amount * downPaymentPercent;
    }
    
    const currentAmount = parseFloat(goal.current_amount || '0');
    const remainingAmount = Math.max(0, cashRequired - currentAmount);
    return remainingAmount / monthsRemaining;
  };

  // Basic sanity check for individual goals (Step 3 scope only)
  const getBasicGoalStatus = (goal: Goal) => {
    const targetDate = new Date(goal.target_date);
    const today = new Date();
    const daysRemaining = Math.ceil((targetDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    const monthlySavingsRequired = calculateMonthlySavingsRequired(goal);
    
    // Basic sanity checks only - no complex conflict detection
    return {
      isDateValid: daysRemaining > 0,
      monthlySavingsRequired,
      isAmountRealistic: monthlySavingsRequired < 50000, // Basic threshold
      message: daysRemaining <= 0 ? 'Target date has passed' : 
               monthlySavingsRequired > 50000 ? 'Very high monthly requirement' : ''
    };
  };

  // Event handlers
  const handleDeleteGoal = async (goal: Goal) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete the goal "${goal.name}"?\n\nThis action cannot be undone.`
    );
    
    if (confirmed) {
      try {
        await deleteGoalMutation.mutateAsync(goal.goal_id);
      } catch (error) {
        console.error('Failed to delete goal:', error);
        alert('Failed to delete goal. Please try again.');
      }
    }
  };

  const handleEditGoal = (goal: Goal) => {
    console.log('🔧 Edit button clicked for goal:', goal);
    console.log('🔧 Setting selectedGoal to:', goal);
    console.log('🔧 Current showAddGoal state:', showAddGoal);
    setSelectedGoal(goal);
    setShowAddGoal(true); // Reuse the add goal form for editing
    console.log('🔧 Should now show modal with showAddGoal=true and selectedGoal=', goal);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">Error loading goals. Please try again.</p>
        <Button onClick={() => refetch()}>Retry</Button>
      </div>
    );
  }

  return (
    <div className={`goal-manager ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <Target className="w-8 h-8 text-blue-500" />
              Financial Goals
            </h1>
            <p className="text-gray-300 mt-1">Track and achieve your financial objectives</p>
          </div>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => setShowPreferences(true)}
              className="flex items-center gap-2"
            >
              <Settings className="w-4 h-4" />
              Preferences
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                try {
                  const response = await fetch('/api/v1/sync-net-worth', {
                    method: 'POST',
                    headers: {
                      'Authorization': `Bearer ${localStorage.getItem('auth_tokens') ? JSON.parse(localStorage.getItem('auth_tokens')!).access_token : ''}`,
                      'Content-Type': 'application/json'
                    }
                  });
                  if (response.ok) {
                    const result = await response.json();
                    alert(result.message);
                    refetch(); // Refresh goals list
                  } else {
                    alert('Failed to sync net worth. Please try again.');
                  }
                } catch (error) {
                  alert('Error syncing net worth. Please try again.');
                }
              }}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white"
            >
              <TrendingUp className="w-4 h-4" />
              Sync Net Worth
            </Button>
            <Button
              onClick={() => setShowAddGoal(true)}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Add Goal
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card className="bg-gradient-to-r from-blue-900 to-blue-800">
              <Card.Body className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-200 text-sm">Active Goals</p>
                    <p className="text-2xl font-bold text-white">{summary.active_goals}</p>
                  </div>
                  <Target className="w-8 h-8 text-blue-400" />
                </div>
              </Card.Body>
            </Card>

            <Card className="bg-gradient-to-r from-green-900 to-green-800">
              <Card.Body className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-green-200 text-sm">Achieved</p>
                    <p className="text-2xl font-bold text-white">{summary.achieved_goals}</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-400" />
                </div>
              </Card.Body>
            </Card>

            <Card className="bg-gradient-to-r from-purple-900 to-purple-800">
              <Card.Body className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-200 text-sm">Total Target</p>
                    <p className="text-2xl font-bold text-white">{formatCurrency(summary.total_target)}</p>
                  </div>
                  <Target className="w-8 h-8 text-purple-400" />
                </div>
              </Card.Body>
            </Card>

            <Card className="bg-gradient-to-r from-orange-900 to-orange-800">
              <Card.Body className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-orange-200 text-sm">Avg Progress</p>
                    <p className="text-2xl font-bold text-white">{summary.average_progress.toFixed(1)}%</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-orange-400" />
                </div>
              </Card.Body>
            </Card>
          </div>
        )}

        {/* Step 4 Intelligence Analysis Teaser */}
        {goals.length > 1 && (
          <Card className="mb-6 border-blue-600 bg-blue-900/20">
            <Card.Body className="p-4">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-6 h-6 text-blue-500" />
                <div>
                  <h3 className="text-lg font-semibold text-blue-100">Ready for Intelligence Analysis</h3>
                  <p className="text-blue-200">
                    Complete comprehensive analysis of all your goals together in Step 4.
                  </p>
                </div>
                <Button variant="outline" size="sm" className="ml-auto">
                  Continue to Step 4
                </Button>
              </div>
            </Card.Body>
          </Card>
        )}

        {/* Filters */}
        <div className="flex gap-4 items-center mb-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-gray-300 text-sm">Filters:</span>
          </div>
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-gray-700 border border-gray-600 text-white rounded px-3 py-1 text-sm"
          >
            <option value="">All Statuses</option>
            {Object.entries(GOAL_STATUSES).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-gray-700 border border-gray-600 text-white rounded px-3 py-1 text-sm"
          >
            <option value="">All Categories</option>
            {Object.entries(GOAL_CATEGORIES).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>

          {(statusFilter || categoryFilter) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setStatusFilter('');
                setCategoryFilter('');
              }}
              className="text-gray-400 hover:text-white"
            >
              Clear Filters
            </Button>
          )}
          
          {/* View Toggle */}
          <div className="flex items-center bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                viewMode === 'list'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              List
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                viewMode === 'timeline'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Timeline
            </button>
          </div>
        </div>
      </div>

      {/* Goals Display */}
      <div className="space-y-4">
        {viewMode === 'timeline' ? (
          // Timeline View
          <Card>
            <Card.Body className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Goal Timeline</h3>
              {goals.length === 0 ? (
                <div className="text-center py-8 text-gray-400">No goals to display</div>
              ) : (
                <div className="relative">
                  <div className="flex justify-between text-sm text-gray-400 mb-4">
                    <span>2024</span>
                    <span>2030</span>
                    <span>2040</span>
                  </div>
                  
                  <div className="relative bg-gray-700 h-2 rounded-full mb-8">
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-green-500 h-full rounded-full opacity-50"></div>
                  </div>
                  
                  <div className="space-y-4">
                    {goals
                      .sort((a, b) => new Date(a.target_date).getTime() - new Date(b.target_date).getTime())
                      .map((goal) => {
                        const targetDate = new Date(goal.target_date);
                        const currentYear = new Date().getFullYear();
                        const targetYear = targetDate.getFullYear();
                        const yearsFromNow = targetYear - currentYear;
                        
                        return (
                          <div key={goal.goal_id} className="flex items-center gap-4 p-3 bg-gray-800/50 rounded-lg">
                            <div className="text-2xl">{getCategoryEmoji(goal.category)}</div>
                            <div className="flex-1">
                              <h4 className="font-semibold text-white">{goal.name}</h4>
                              <div className="flex items-center gap-4 text-sm text-gray-400">
                                <span>{formatCurrency(goal.target_amount)} by {targetYear}</span>
                                <span className="px-2 py-1 bg-blue-900/50 rounded text-blue-300">
                                  {yearsFromNow} years
                                </span>
                                <span className={`px-2 py-1 rounded ${getPriorityBadgeColor(goal.priority)}`}>
                                  {getPriorityLabel(goal.priority)}
                                </span>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm text-gray-400">Progress</div>
                              <div className="text-lg font-bold text-blue-400">
                                {(goal.progress_percentage || 0).toFixed(1)}%
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}
            </Card.Body>
          </Card>
        ) : (
          // List View
          <div className="space-y-4">
        {goals.length === 0 ? (
          <Card>
            <Card.Body className="text-center py-12">
              <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-100 mb-2">No Goals Yet</h3>
              <p className="text-gray-400 mb-6">
                Start by creating your first financial goal to track your progress.
              </p>
              <Button onClick={() => setShowAddGoal(true)}>
                Create Your First Goal
              </Button>
            </Card.Body>
          </Card>
        ) : (
          goals.map((goal) => {
            const daysUntil = getDaysUntilTarget(goal.target_date);
            const progress = goal.progress_percentage || 0;
            
            const monthlySavingsRequired = calculateMonthlySavingsRequired(goal);
            const basicStatus = getBasicGoalStatus(goal);
            
            return (
              <Card key={goal.goal_id} className="hover:border-blue-600 transition-colors">
                <Card.Body className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="text-4xl">{getCategoryEmoji(goal.category)}</div>
                      <div>
                        <h3 className="text-xl font-semibold text-white">
                          {goal.name}
                        </h3>
                        <div className="flex items-center gap-3 mt-1">
                          <Badge variant="secondary">
                            {GOAL_CATEGORIES[goal.category as keyof typeof GOAL_CATEGORIES]}
                          </Badge>
                          <Badge className={getPriorityBadgeColor(goal.priority)}>
                            {getPriorityLabel(goal.priority)}
                          </Badge>
                          <Badge 
                            variant={goal.status === 'active' ? 'default' : 'secondary'}
                          >
                            {GOAL_STATUSES[goal.status as keyof typeof GOAL_STATUSES]}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedGoal(goal)}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          console.log('🔧 Edit button CLICKED!', goal.name);
                          handleEditGoal(goal);
                        }}
                      >
                        <Edit3 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-400 hover:text-red-300"
                        onClick={() => handleDeleteGoal(goal)}
                        disabled={deleteGoalMutation.isPending}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <div>
                      {goal.category === 'real_estate' ? (
                        <>
                          <p className="text-gray-400 text-sm">Property Value</p>
                          <p className="text-lg font-bold text-white">{formatCurrency(goal.target_amount)}</p>
                          <p className="text-xs text-blue-400">
                            Cash needed: {formatCurrency(getCashRequired(goal))} ({goal.params?.down_payment_percentage || 20}% down)
                          </p>
                        </>
                      ) : (
                        <>
                          <p className="text-gray-400 text-sm">Target Amount</p>
                          <p className="text-lg font-bold text-white">{formatCurrency(goal.target_amount)}</p>
                        </>
                      )}
                    </div>
                    
                    <div>
                      <p className="text-gray-400 text-sm">Current Amount</p>
                      <p className="text-lg font-bold text-white">{formatCurrency(goal.current_amount || 0)}</p>
                    </div>
                    
                    <div>
                      <p className="text-gray-400 text-sm">Monthly Required</p>
                      <p className="text-lg font-bold text-blue-400">{formatCurrency(monthlySavingsRequired)}</p>
                      <p className="text-xs text-gray-500">to reach goal</p>
                    </div>
                    
                    <div>
                      <p className="text-gray-400 text-sm">Target Date</p>
                      <p className="text-lg font-bold text-white">{formatDate(goal.target_date)}</p>
                      <p className={`text-sm ${daysUntil < 90 ? 'text-red-400' : 'text-gray-400'}`}>
                        {daysUntil > 0 ? `${daysUntil} days left` : 'Overdue'}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-gray-400 text-sm">Progress</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all"
                            style={{ width: `${Math.min(progress, 100)}%` }}
                          />
                        </div>
                        <span className={`text-sm font-bold ${getProgressColor(progress)}`}>
                          {progress.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Basic Status Check (Step 3 scope only) */}
                  {basicStatus.message && (
                    <div className="mt-4 p-3 bg-orange-900/20 border border-orange-600 rounded-lg">
                      <div className="flex items-start gap-2">
                        <span className="text-orange-400 mt-0.5">ℹ️</span>
                        <div>
                          <p className="text-orange-300 font-medium text-sm">Goal Notice:</p>
                          <p className="text-orange-200 text-xs mt-1">{basicStatus.message}</p>
                          <p className="text-orange-200 text-xs mt-1">
                            💡 Complete Step 4 for comprehensive goal analysis
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </Card.Body>
              </Card>
            );
          })
        )}
          </div>
        )}
      </div>

      {/* Modals */}
      {showAddGoal && (
        <GoalForm
          goal={selectedGoal} // Pass selected goal for editing
          onClose={() => {
            console.log('🔄 GoalForm onClose called');
            setShowAddGoal(false);
            setSelectedGoal(null);
          }}
          onSuccess={() => {
            console.log('🔄 GoalForm onSuccess called');
            setShowAddGoal(false);
            setSelectedGoal(null);
            refetch();
          }}
        />
      )}

      {showPreferences && (
        <UserPreferencesForm
          onClose={() => setShowPreferences(false)}
        />
      )}

      {selectedGoal && !showAddGoal && (
        <GoalDetails
          goal={selectedGoal}
          onClose={() => setSelectedGoal(null)}
        />
      )}
    </div>
  );
};

export default GoalManager;