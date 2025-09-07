/**
 * WealthPath AI - Goal Details Component
 * Detailed view of a goal with progress tracking and history
 */
import React, { useState } from 'react';
import { 
  X, 
  Target, 
  TrendingUp, 
  Calendar, 
  DollarSign, 
  Plus,
  Edit3,
  History,
  ChevronRight
} from 'lucide-react';

import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Input from '../ui/Input';
import { 
  useGoalProgressQuery, 
  useGoalHistoryQuery, 
  useRecordProgressMutation 
} from '../../hooks/use-goal-queries';
import { GOAL_CATEGORIES, GOAL_STATUSES } from '../../types/goals';
import type { Goal } from '../../types/goals';

interface GoalDetailsProps {
  goal: Goal;
  onClose: () => void;
  onEdit?: (goal: Goal) => void;
}

const GoalDetails: React.FC<GoalDetailsProps> = ({ goal, onClose, onEdit }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'progress' | 'history'>('overview');
  const [showAddProgress, setShowAddProgress] = useState(false);
  const [progressAmount, setProgressAmount] = useState('');
  const [progressNotes, setProgressNotes] = useState('');

  const { data: progressHistory = [] } = useGoalProgressQuery(goal.goal_id, 10);
  const { data: history = [] } = useGoalHistoryQuery(goal.goal_id);
  const recordProgressMutation = useRecordProgressMutation();

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

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getDaysUntilTarget = (targetDate: string) => {
    const today = new Date();
    const target = new Date(targetDate);
    const diffTime = target.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const calculateMonthlyRequired = () => {
    const remainingAmount = goal.target_amount - (goal.current_amount || 0);
    const daysLeft = getDaysUntilTarget(goal.target_date);
    const monthsLeft = Math.max(1, daysLeft / 30.44);
    return remainingAmount / monthsLeft;
  };

  const handleAddProgress = async () => {
    if (!progressAmount) return;

    try {
      await recordProgressMutation.mutateAsync({
        goalId: goal.goal_id,
        progress: {
          current_amount: parseFloat(progressAmount),
          notes: progressNotes || undefined,
        },
      });

      setProgressAmount('');
      setProgressNotes('');
      setShowAddProgress(false);
    } catch (error) {
      console.error('Failed to record progress:', error);
      alert('Failed to record progress. Please try again.');
    }
  };

  const progress = goal.progress_percentage || 0;
  const daysUntil = getDaysUntilTarget(goal.target_date);
  const monthlyRequired = calculateMonthlyRequired();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Target className="w-6 h-6 text-white" />
              <div>
                <h2 className="text-xl font-bold text-white">{goal.name}</h2>
                <p className="text-blue-100">
                  {GOAL_CATEGORIES[goal.category as keyof typeof GOAL_CATEGORIES]}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={() => onEdit?.(goal)}
                className="text-white border-white/30 hover:bg-white/10"
              >
                <Edit3 className="w-4 h-4 mr-2" />
                Edit Goal
              </Button>
              <button
                onClick={onClose}
                className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-700">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'overview', label: 'Overview', icon: Target },
              { id: 'progress', label: 'Progress', icon: TrendingUp },
              { id: 'history', label: 'History', icon: History },
            ].map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-400 hover:text-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Progress Summary */}
              <Card>
                <Card.Body className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Progress Summary</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div>
                      <p className="text-gray-400 text-sm">Target Amount</p>
                      <p className="text-2xl font-bold text-white">{formatCurrency(goal.target_amount)}</p>
                    </div>
                    
                    <div>
                      <p className="text-gray-400 text-sm">Current Amount</p>
                      <p className="text-2xl font-bold text-green-400">{formatCurrency(goal.current_amount || 0)}</p>
                    </div>
                    
                    <div>
                      <p className="text-gray-400 text-sm">Remaining</p>
                      <p className="text-2xl font-bold text-orange-400">
                        {formatCurrency(goal.target_amount - (goal.current_amount || 0))}
                      </p>
                    </div>
                    
                    <div>
                      <p className="text-gray-400 text-sm">Progress</p>
                      <div className="flex items-center gap-3">
                        <div className="flex-1 bg-gray-700 rounded-full h-3">
                          <div
                            className="bg-blue-500 h-3 rounded-full transition-all"
                            style={{ width: `${Math.min(progress, 100)}%` }}
                          />
                        </div>
                        <span className="text-lg font-bold text-blue-400">
                          {progress.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </Card.Body>
              </Card>

              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <Card.Body className="p-4 text-center">
                    <Calendar className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                    <p className="text-gray-400 text-sm">Target Date</p>
                    <p className="text-lg font-bold text-white">{formatDate(goal.target_date)}</p>
                    <p className={`text-sm ${daysUntil < 90 ? 'text-red-400' : 'text-gray-400'}`}>
                      {daysUntil > 0 ? `${daysUntil} days left` : 'Overdue'}
                    </p>
                  </Card.Body>
                </Card>

                <Card>
                  <Card.Body className="p-4 text-center">
                    <DollarSign className="w-8 h-8 text-green-500 mx-auto mb-2" />
                    <p className="text-gray-400 text-sm">Monthly Required</p>
                    <p className="text-lg font-bold text-white">{formatCurrency(monthlyRequired)}</p>
                    <p className="text-sm text-gray-400">to reach goal</p>
                  </Card.Body>
                </Card>

                <Card>
                  <Card.Body className="p-4 text-center">
                    <Target className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                    <p className="text-gray-400 text-sm">Priority</p>
                    <p className="text-lg font-bold text-white">{goal.priority}/10</p>
                    <Badge className="mt-1">
                      {GOAL_STATUSES[goal.status as keyof typeof GOAL_STATUSES]}
                    </Badge>
                  </Card.Body>
                </Card>
              </div>

              {/* Goal Parameters */}
              {goal.params && Object.keys(goal.params).length > 0 && (
                <Card>
                  <Card.Body className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Goal Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {Object.entries(goal.params).map(([key, value]) => (
                        <div key={key}>
                          <p className="text-gray-400 text-sm">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </p>
                          <p className="text-white font-medium">
                            {typeof value === 'number' && key.includes('amount') 
                              ? formatCurrency(value)
                              : String(value)
                            }
                          </p>
                        </div>
                      ))}
                    </div>
                  </Card.Body>
                </Card>
              )}
            </div>
          )}

          {activeTab === 'progress' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-white">Progress History</h3>
                <Button
                  onClick={() => setShowAddProgress(true)}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Record Progress
                </Button>
              </div>

              {showAddProgress && (
                <Card className="border-blue-600">
                  <Card.Body className="p-4">
                    <h4 className="font-semibold text-white mb-4">Record New Progress</h4>
                    <div className="space-y-4">
                      <Input
                        label="Current Amount"
                        type="number"
                        value={progressAmount}
                        onChange={(e) => setProgressAmount(e.target.value)}
                        leftIcon={<DollarSign className="w-4 h-4" />}
                        placeholder="Enter current total amount"
                        min="0"
                        step="0.01"
                      />
                      <Input
                        label="Notes (Optional)"
                        value={progressNotes}
                        onChange={(e) => setProgressNotes(e.target.value)}
                        placeholder="Add notes about this progress update..."
                      />
                      <div className="flex gap-3">
                        <Button
                          onClick={handleAddProgress}
                          disabled={!progressAmount || recordProgressMutation.isPending}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          {recordProgressMutation.isPending ? 'Recording...' : 'Record Progress'}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => setShowAddProgress(false)}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  </Card.Body>
                </Card>
              )}

              <div className="space-y-3">
                {progressHistory.length === 0 ? (
                  <Card>
                    <Card.Body className="text-center py-8">
                      <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-400">No progress recorded yet</p>
                      <p className="text-gray-500 text-sm">Start tracking your progress towards this goal</p>
                    </Card.Body>
                  </Card>
                ) : (
                  progressHistory.map((entry) => (
                    <Card key={entry.progress_id}>
                      <Card.Body className="p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="text-lg font-semibold text-white">
                              {formatCurrency(entry.current_amount)}
                            </p>
                            <p className="text-blue-400 font-medium">
                              {entry.percentage_complete.toFixed(1)}% complete
                            </p>
                            {entry.notes && (
                              <p className="text-gray-300 text-sm mt-2">{entry.notes}</p>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="text-gray-400 text-sm">{formatDateTime(entry.recorded_at)}</p>
                            <Badge variant="secondary" size="sm">
                              {entry.source}
                            </Badge>
                          </div>
                        </div>
                      </Card.Body>
                    </Card>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white">Change History</h3>
              
              <div className="space-y-3">
                {history.length === 0 ? (
                  <Card>
                    <Card.Body className="text-center py-8">
                      <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-400">No history available</p>
                    </Card.Body>
                  </Card>
                ) : (
                  history.map((entry) => (
                    <Card key={entry.history_id}>
                      <Card.Body className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <Badge 
                              variant={entry.change_type === 'created' ? 'default' : 'secondary'}
                              size="sm"
                            >
                              {entry.change_type}
                            </Badge>
                            <span className="text-gray-400 text-sm">by {entry.actor}</span>
                          </div>
                          <span className="text-gray-400 text-sm">
                            {formatDateTime(entry.changed_at)}
                          </span>
                        </div>
                        
                        {entry.reason && (
                          <p className="text-gray-300 text-sm mb-2">{entry.reason}</p>
                        )}
                        
                        {/* Simplified diff display */}
                        {entry.change_type === 'updated' && entry.diff.old && entry.diff.new && (
                          <details className="text-xs text-gray-400">
                            <summary className="cursor-pointer hover:text-gray-300">
                              View Changes <ChevronRight className="inline w-3 h-3" />
                            </summary>
                            <div className="mt-2 p-2 bg-gray-900 rounded">
                              <pre className="text-xs overflow-x-auto">
                                {JSON.stringify(entry.diff, null, 2)}
                              </pre>
                            </div>
                          </details>
                        )}
                      </Card.Body>
                    </Card>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GoalDetails;