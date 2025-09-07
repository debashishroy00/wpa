/**
 * WealthPath AI - Timeline Tab
 * Visual timeline showing when each goal will be achieved
 */
import React, { useState } from 'react';
import { 
  Calendar, 
  Target, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  DollarSign,
  Filter,
  Eye,
  EyeOff
} from 'lucide-react';
import Card from '../../ui/Card';
import Badge from '../../ui/Badge';
import Button from '../../ui/Button';

interface TimelineGoal {
  goal_id: string;
  name: string;
  category: string;
  target_date: string;
  current_amount: number;
  target_amount: number;
  monthly_required: number;
  feasibility_score: number;
  milestones: Array<{
    date: string;
    amount: number;
    percentage: number;
    description: string;
  }>;
  status: 'on_track' | 'at_risk' | 'behind' | 'completed';
}

interface TimelineTabProps {
  timeline: {
    goals: TimelineGoal[];
    major_milestones: Array<{
      date: string;
      type: string;
      description: string;
      goals_affected: string[];
    }>;
  };
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short'
  });
};

const getCategoryEmoji = (category: string): string => {
  const emojiMap: Record<string, string> = {
    'retirement': '🏖️',
    'real_estate': '🏠',
    'education': '🎓',
    'business': '🚀',
    'emergency_fund': '🛡️',
    'vacation': '🏝️',
    'vehicle': '🚗',
    'health': '💊',
    'other': '💰'
  };
  return emojiMap[category] || '💰';
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
      return 'text-green-400 bg-green-400';
    case 'on_track':
      return 'text-blue-400 bg-blue-400';
    case 'at_risk':
      return 'text-yellow-400 bg-yellow-400';
    case 'behind':
      return 'text-red-400 bg-red-400';
    default:
      return 'text-gray-400 bg-gray-400';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4" />;
    case 'on_track':
      return <Target className="w-4 h-4" />;
    case 'at_risk':
    case 'behind':
      return <AlertTriangle className="w-4 h-4" />;
    default:
      return <Clock className="w-4 h-4" />;
  }
};

interface TimelineItemProps {
  goal: TimelineGoal;
  isVisible: boolean;
}

const TimelineItem: React.FC<TimelineItemProps> = ({ goal, isVisible }) => {
  const [showMilestones, setShowMilestones] = useState(false);
  const currentYear = new Date().getFullYear();
  const targetYear = new Date(goal.target_date).getFullYear();
  const yearsToTarget = targetYear - currentYear;
  
  // Calculate progress
  const progressPercentage = (goal.current_amount / goal.target_amount) * 100;

  if (!isVisible) return null;

  return (
    <div className="flex gap-6 pb-6">
      {/* Timeline Connector */}
      <div className="flex flex-col items-center">
        <div className={`w-4 h-4 rounded-full border-2 ${getStatusColor(goal.status).split(' ')[1]} border-current`}>
          <div className={`w-2 h-2 rounded-full ${getStatusColor(goal.status).split(' ')[1]} m-0.5`}></div>
        </div>
        <div className="w-0.5 bg-gray-600 flex-1 min-h-20"></div>
      </div>

      {/* Goal Card */}
      <div className="flex-1">
        <Card className={`hover:border-blue-600 transition-colors ${goal.status === 'completed' ? 'bg-green-900/10' : ''}`}>
          <Card.Body className="p-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{getCategoryEmoji(goal.category)}</span>
                <div>
                  <h4 className="text-lg font-semibold text-white">{goal.name}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge
                      variant={goal.status === 'completed' ? 'success' : 
                              goal.status === 'on_track' ? 'info' : 
                              goal.status === 'at_risk' ? 'warning' : 'error'}
                      size="sm"
                    >
                      {getStatusIcon(goal.status)}
                      {goal.status.replace('_', ' ').toUpperCase()}
                    </Badge>
                    <span className="text-sm text-gray-400">
                      Target: {formatDate(goal.target_date)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-400">Feasibility</div>
                <div className={`text-lg font-bold ${goal.feasibility_score >= 80 ? 'text-green-400' : 
                                                     goal.feasibility_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {Math.round(goal.feasibility_score)}%
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-3">
              <div className="flex justify-between text-sm text-gray-400 mb-1">
                <span>Progress</span>
                <span>{formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${goal.status === 'completed' ? 'bg-green-500' :
                                                   goal.status === 'on_track' ? 'bg-blue-500' :
                                                   goal.status === 'at_risk' ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {Math.round(progressPercentage)}% complete
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-3 gap-4 mb-3">
              <div className="text-center">
                <div className="text-sm text-gray-400">Monthly Need</div>
                <div className="text-white font-semibold">{formatCurrency(goal.monthly_required)}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-400">Remaining</div>
                <div className="text-white font-semibold">
                  {formatCurrency(goal.target_amount - goal.current_amount)}
                </div>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-400">Time Left</div>
                <div className="text-white font-semibold">
                  {yearsToTarget} year{yearsToTarget !== 1 ? 's' : ''}
                </div>
              </div>
            </div>

            {/* Milestones Toggle */}
            {goal.milestones.length > 0 && (
              <div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setShowMilestones(!showMilestones)}
                  className="text-gray-300 hover:text-white"
                >
                  {showMilestones ? <EyeOff className="w-3 h-3 mr-1" /> : <Eye className="w-3 h-3 mr-1" />}
                  {showMilestones ? 'Hide' : 'Show'} Milestones ({goal.milestones.length})
                </Button>

                {showMilestones && (
                  <div className="mt-3 space-y-2">
                    {goal.milestones.map((milestone, index) => (
                      <div key={index} className="flex items-center gap-3 p-2 bg-gray-700/50 rounded">
                        <div className="w-2 h-2 bg-blue-400 rounded-full flex-shrink-0"></div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-gray-300">{milestone.description}</span>
                            <span className="text-xs text-gray-400">{formatDate(milestone.date)}</span>
                          </div>
                          <div className="text-xs text-gray-400">
                            {formatCurrency(milestone.amount)} ({milestone.percentage}%)
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </Card.Body>
        </Card>
      </div>
    </div>
  );
};

export const TimelineTab: React.FC<TimelineTabProps> = ({ timeline }) => {
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [selectedStatuses, setSelectedStatuses] = useState<Set<string>>(new Set());
  
  const categories = [...new Set(timeline.goals.map(g => g.category))];
  const statuses = [...new Set(timeline.goals.map(g => g.status))];

  // Sort goals by target date
  const sortedGoals = [...timeline.goals].sort((a, b) => 
    new Date(a.target_date).getTime() - new Date(b.target_date).getTime()
  );

  // Filter goals based on selected categories and statuses
  const filteredGoals = sortedGoals.filter(goal => {
    const categoryMatch = selectedCategories.size === 0 || selectedCategories.has(goal.category);
    const statusMatch = selectedStatuses.size === 0 || selectedStatuses.has(goal.status);
    return categoryMatch && statusMatch;
  });

  const toggleCategoryFilter = (category: string) => {
    const newSet = new Set(selectedCategories);
    if (newSet.has(category)) {
      newSet.delete(category);
    } else {
      newSet.add(category);
    }
    setSelectedCategories(newSet);
  };

  const toggleStatusFilter = (status: string) => {
    const newSet = new Set(selectedStatuses);
    if (newSet.has(status)) {
      newSet.delete(status);
    } else {
      newSet.add(status);
    }
    setSelectedStatuses(newSet);
  };

  if (timeline.goals.length === 0) {
    return (
      <Card className="text-center py-12">
        <Card.Body>
          <div className="text-6xl mb-4">📅</div>
          <h3 className="text-2xl font-semibold text-white mb-4">No Timeline Data</h3>
          <p className="text-gray-300 mb-6">
            Add some financial goals to see your personalized timeline.
          </p>
          <Button className="bg-blue-600 hover:bg-blue-700">
            Add Your First Goal
          </Button>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border-purple-600">
        <Card.Body className="p-6">
          <div className="flex items-center gap-4">
            <Calendar className="w-8 h-8 text-purple-400" />
            <div>
              <h3 className="text-xl font-semibold text-purple-100 mb-1">
                Goal Achievement Timeline
              </h3>
              <p className="text-purple-200">
                Track progress and projected completion dates for all your financial goals.
              </p>
            </div>
          </div>

          {/* Summary Stats */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">
                {timeline.goals.filter(g => g.status === 'completed').length}
              </div>
              <div className="text-xs text-gray-400">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">
                {timeline.goals.filter(g => g.status === 'on_track').length}
              </div>
              <div className="text-xs text-gray-400">On Track</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">
                {timeline.goals.filter(g => g.status === 'at_risk').length}
              </div>
              <div className="text-xs text-gray-400">At Risk</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">
                {timeline.goals.filter(g => g.status === 'behind').length}
              </div>
              <div className="text-xs text-gray-400">Behind</div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Filters */}
      <Card className="bg-gray-800">
        <Card.Body className="p-4">
          <div className="flex items-center gap-4 mb-4">
            <Filter className="w-5 h-5 text-gray-400" />
            <h4 className="font-semibold text-white">Filters</h4>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                setSelectedCategories(new Set());
                setSelectedStatuses(new Set());
              }}
              className="ml-auto text-xs"
            >
              Clear All
            </Button>
          </div>

          <div className="space-y-3">
            {/* Category Filters */}
            <div>
              <div className="text-sm text-gray-400 mb-2">Categories:</div>
              <div className="flex flex-wrap gap-2">
                {categories.map(category => (
                  <button
                    key={category}
                    onClick={() => toggleCategoryFilter(category)}
                    className={`
                      px-3 py-1 rounded-full text-xs font-medium border transition-colors
                      ${selectedCategories.has(category) ? 
                        'bg-blue-600 text-white border-blue-600' : 
                        'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'}
                    `}
                  >
                    {getCategoryEmoji(category)} {category.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>

            {/* Status Filters */}
            <div>
              <div className="text-sm text-gray-400 mb-2">Status:</div>
              <div className="flex flex-wrap gap-2">
                {statuses.map(status => (
                  <button
                    key={status}
                    onClick={() => toggleStatusFilter(status)}
                    className={`
                      px-3 py-1 rounded-full text-xs font-medium border transition-colors
                      ${selectedStatuses.has(status) ? 
                        'bg-blue-600 text-white border-blue-600' : 
                        'bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600'}
                    `}
                  >
                    {getStatusIcon(status)} {status.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Timeline */}
      <Card className="bg-gray-800">
        <Card.Body className="p-6">
          <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-400" />
            Timeline View ({filteredGoals.length} goals)
          </h3>

          {filteredGoals.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-4xl mb-2">🔍</div>
              <p className="text-gray-300">No goals match your current filters.</p>
              <p className="text-sm text-gray-400 mt-1">Try adjusting your filter selection.</p>
            </div>
          ) : (
            <div className="relative">
              {filteredGoals.map((goal, index) => (
                <TimelineItem
                  key={goal.goal_id}
                  goal={goal}
                  isVisible={true}
                />
              ))}
              
              {/* Timeline End */}
              <div className="flex gap-6">
                <div className="flex flex-col items-center">
                  <div className="w-4 h-4 rounded-full bg-gray-600"></div>
                </div>
                <div className="text-sm text-gray-400 pb-4">
                  🎯 All goals timeline complete
                </div>
              </div>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Major Milestones */}
      {timeline.major_milestones.length > 0 && (
        <Card className="bg-gradient-to-r from-indigo-900/20 to-purple-900/20 border-indigo-600">
          <Card.Body className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-indigo-400" />
              Major Milestones
            </h3>
            
            <div className="space-y-3">
              {timeline.major_milestones.map((milestone, index) => (
                <div key={index} className="flex items-start gap-3 p-3 bg-gray-700/50 rounded-lg">
                  <div className="bg-indigo-600 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold flex-shrink-0">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="text-white font-medium">{milestone.type.replace('_', ' ').toUpperCase()}</h4>
                      <span className="text-sm text-gray-400">{formatDate(milestone.date)}</span>
                    </div>
                    <p className="text-gray-300 text-sm mb-2">{milestone.description}</p>
                    <div className="flex flex-wrap gap-1">
                      {milestone.goals_affected.map((goalId, goalIndex) => {
                        const goal = timeline.goals.find(g => g.goal_id === goalId);
                        return (
                          <Badge key={goalIndex} variant="secondary" size="sm">
                            {goal ? goal.name : goalId}
                          </Badge>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};