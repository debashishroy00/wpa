/**
 * WealthPath AI - Recommendations Tab
 * Shows personalized recommendations with tracking capabilities
 */
import React, { useState } from 'react';
import { 
  CheckSquare, 
  Target, 
  Clock, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  XCircle,
  Eye,
  Star,
  ArrowRight,
  DollarSign,
  Calendar,
  BarChart3
} from 'lucide-react';
import Card from '../../ui/Card';
import Badge from '../../ui/Badge';
import Button from '../../ui/Button';
import { useRecommendationActionMutation } from '../../../hooks/use-intelligence-hooks';

interface Recommendation {
  id: string;
  type: 'immediate' | 'short_term' | 'long_term';
  category: string;
  title: string;
  description: string;
  impact_description: string;
  projected_impact: {
    success_rate_improvement: number;
    cost_reduction?: number;
    time_saved?: number;
    additional_savings?: number;
  };
  difficulty: 'easy' | 'moderate' | 'hard';
  estimated_time: string;
  prerequisites?: string[];
  action_steps: string[];
  priority: 'high' | 'medium' | 'low';
  status: 'new' | 'viewed' | 'accepted' | 'rejected' | 'completed';
  goals_affected: string[];
}

interface RecommendationsTabProps {
  recommendations: {
    immediate: Recommendation[];
    short_term: Recommendation[];
    long_term: Recommendation[];
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

const getTypeColor = (type: string): string => {
  switch (type) {
    case 'immediate':
      return 'from-red-900/30 to-orange-900/30 border-red-600';
    case 'short_term':
      return 'from-yellow-900/30 to-orange-900/30 border-yellow-600';
    case 'long_term':
      return 'from-blue-900/30 to-indigo-900/30 border-blue-600';
    default:
      return 'from-gray-900/30 to-gray-800/30 border-gray-600';
  }
};

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'immediate':
      return <AlertCircle className="w-5 h-5 text-red-400" />;
    case 'short_term':
      return <Clock className="w-5 h-5 text-yellow-400" />;
    case 'long_term':
      return <Target className="w-5 h-5 text-blue-400" />;
    default:
      return <CheckSquare className="w-5 h-5 text-gray-400" />;
  }
};

const getPriorityColor = (priority: string): string => {
  switch (priority) {
    case 'high':
      return 'text-red-400 bg-red-400';
    case 'medium':
      return 'text-yellow-400 bg-yellow-400';
    case 'low':
      return 'text-green-400 bg-green-400';
    default:
      return 'text-gray-400 bg-gray-400';
  }
};

const getDifficultyColor = (difficulty: string): string => {
  switch (difficulty) {
    case 'easy':
      return 'text-green-400';
    case 'moderate':
      return 'text-yellow-400';
    case 'hard':
      return 'text-red-400';
    default:
      return 'text-gray-400';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    case 'accepted':
      return <CheckSquare className="w-4 h-4 text-blue-400" />;
    case 'rejected':
      return <XCircle className="w-4 h-4 text-red-400" />;
    case 'viewed':
      return <Eye className="w-4 h-4 text-yellow-400" />;
    default:
      return <Star className="w-4 h-4 text-gray-400" />;
  }
};

interface RecommendationCardProps {
  recommendation: Recommendation;
  onStatusChange: (id: string, status: string, notes?: string) => void;
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ 
  recommendation, 
  onStatusChange 
}) => {
  const [expanded, setExpanded] = useState(false);
  const [notes, setNotes] = useState('');

  const handleStatusChange = (newStatus: string) => {
    onStatusChange(recommendation.id, newStatus, notes);
  };

  return (
    <Card className={`bg-gradient-to-r ${getTypeColor(recommendation.type)} transition-all duration-300 hover:shadow-lg`}>
      <Card.Body className="p-6">
        {/* Header */}
        <div className="flex items-start gap-4 mb-4">
          <div className="flex-shrink-0">
            {getTypeIcon(recommendation.type)}
          </div>
          
          <div className="flex-1">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="text-lg font-semibold text-white mb-1">{recommendation.title}</h4>
                <div className="flex items-center gap-2 mb-2">
                  <Badge 
                    variant={recommendation.priority === 'high' ? 'error' : 
                            recommendation.priority === 'medium' ? 'warning' : 'success'} 
                    size="sm"
                  >
                    {(recommendation.priority || 'medium').toUpperCase()}
                  </Badge>
                  <Badge variant="secondary" size="sm">
                    {(recommendation.type || 'general').replace('_', ' ').toUpperCase()}
                  </Badge>
                  <Badge variant="info" size="sm">
                    {(recommendation.category || 'general').replace('_', ' ')}
                  </Badge>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {getStatusIcon(recommendation.status)}
                <span className="text-xs text-gray-400 capitalize">
                  {(recommendation.status || 'new').replace('_', ' ')}
                </span>
              </div>
            </div>

            <p className="text-gray-300 text-sm mb-3">{recommendation.description}</p>

            {/* Impact Preview */}
            <div className="bg-black/20 rounded-lg p-3 mb-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-green-400" />
                <span className="text-sm font-medium text-green-400">Expected Impact</span>
              </div>
              <p className="text-sm text-gray-300 mb-2">{recommendation.impact_description}</p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="text-center">
                  <div className="text-green-400 font-bold">
                    +{recommendation.projected_impact?.success_rate_improvement || 0}%
                  </div>
                  <div className="text-gray-400">Success Rate</div>
                </div>
                
                {recommendation.projected_impact?.cost_reduction && (
                  <div className="text-center">
                    <div className="text-blue-400 font-bold">
                      -{formatCurrency(recommendation.projected_impact.cost_reduction)}
                    </div>
                    <div className="text-gray-400">Cost Savings</div>
                  </div>
                )}
                
                {recommendation.projected_impact?.time_saved && (
                  <div className="text-center">
                    <div className="text-yellow-400 font-bold">
                      -{recommendation.projected_impact.time_saved}mo
                    </div>
                    <div className="text-gray-400">Time Saved</div>
                  </div>
                )}
                
                {recommendation.projected_impact?.additional_savings && (
                  <div className="text-center">
                    <div className="text-purple-400 font-bold">
                      +{formatCurrency(recommendation.projected_impact.additional_savings)}
                    </div>
                    <div className="text-gray-400">Extra Savings</div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Info */}
            <div className="flex items-center gap-4 mb-4 text-sm">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4 text-gray-400" />
                <span className="text-gray-300">{recommendation.estimated_time}</span>
              </div>
              <div className="flex items-center gap-1">
                <BarChart3 className="w-4 h-4 text-gray-400" />
                <span className={getDifficultyColor(recommendation.difficulty)}>
                  {recommendation.difficulty}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <Target className="w-4 h-4 text-gray-400" />
                <span className="text-gray-300">{recommendation.goals_affected?.length || 0} goals</span>
              </div>
            </div>

            {/* Expanded Details */}
            {expanded && (
              <div className="space-y-4">
                {/* Prerequisites */}
                {recommendation.prerequisites && recommendation.prerequisites.length > 0 && (
                  <div>
                    <h5 className="text-sm font-semibold text-gray-300 mb-2">Prerequisites:</h5>
                    <ul className="space-y-1 text-sm text-gray-400">
                      {(recommendation.prerequisites || []).map((prereq, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <div className="w-1 h-1 bg-gray-400 rounded-full mt-2 flex-shrink-0"></div>
                          {prereq}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Action Steps */}
                <div>
                  <h5 className="text-sm font-semibold text-gray-300 mb-2">Action Steps:</h5>
                  <div className="space-y-2">
                    {(recommendation.action_steps || []).map((step, index) => (
                      <div key={index} className="flex items-start gap-3">
                        <div className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold flex-shrink-0">
                          {index + 1}
                        </div>
                        <div className="text-sm text-gray-300 pt-0.5">{step}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Notes for Action Tracking */}
                {recommendation.status !== 'new' && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">
                      Notes (Optional):
                    </label>
                    <textarea
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                      rows={2}
                      placeholder="Add notes about your progress or thoughts..."
                    />
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2 mt-4">
              <Button
                onClick={() => setExpanded(!expanded)}
                variant="outline"
                size="sm"
                className="text-gray-300 hover:text-white"
              >
                {expanded ? 'Less Details' : 'More Details'}
                <ArrowRight className={`w-3 h-3 ml-1 transition-transform ${expanded ? 'rotate-90' : ''}`} />
              </Button>

              {recommendation.status === 'new' && (
                <>
                  <Button
                    onClick={() => handleStatusChange('viewed')}
                    variant="outline"
                    size="sm"
                    className="text-blue-400 hover:text-white"
                  >
                    <Eye className="w-3 h-3 mr-1" />
                    Mark Viewed
                  </Button>
                  <Button
                    onClick={() => handleStatusChange('accepted')}
                    size="sm"
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Accept
                  </Button>
                </>
              )}

              {recommendation.status === 'viewed' && (
                <>
                  <Button
                    onClick={() => handleStatusChange('accepted')}
                    size="sm"
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Accept
                  </Button>
                  <Button
                    onClick={() => handleStatusChange('rejected')}
                    variant="outline"
                    size="sm"
                    className="text-red-400 hover:text-white"
                  >
                    <XCircle className="w-3 h-3 mr-1" />
                    Reject
                  </Button>
                </>
              )}

              {recommendation.status === 'accepted' && (
                <Button
                  onClick={() => handleStatusChange('completed')}
                  size="sm"
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <CheckSquare className="w-3 h-3 mr-1" />
                  Mark Complete
                </Button>
              )}
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export const RecommendationsTab: React.FC<RecommendationsTabProps> = ({ 
  recommendations 
}) => {
  const [activeFilter, setActiveFilter] = useState<'all' | 'immediate' | 'short_term' | 'long_term'>('all');
  const actionMutation = useRecommendationActionMutation();

  const allRecommendations = [
    ...recommendations.immediate,
    ...recommendations.short_term,
    ...recommendations.long_term
  ];

  const filteredRecommendations = activeFilter === 'all' 
    ? allRecommendations
    : allRecommendations.filter(r => r.type === activeFilter);

  const handleStatusChange = async (id: string, status: string, notes?: string) => {
    try {
      await actionMutation.mutateAsync({
        recommendation_id: id,
        action: status as any,
        notes
      });
    } catch (error) {
      console.error('Failed to update recommendation status:', error);
    }
  };

  // Calculate statistics
  const completedCount = allRecommendations.filter(r => r.status === 'completed').length;
  const acceptedCount = allRecommendations.filter(r => r.status === 'accepted').length;
  const pendingCount = allRecommendations.filter(r => ['new', 'viewed'].includes(r.status)).length;

  if (allRecommendations.length === 0) {
    return (
      <Card className="text-center py-12">
        <Card.Body>
          <div className="text-6xl mb-4">✅</div>
          <h3 className="text-2xl font-semibold text-white mb-4">No Recommendations</h3>
          <p className="text-gray-300 mb-6">
            Great job! You're on track with your goals. Check back after running a new analysis.
          </p>
          <Button className="bg-blue-600 hover:bg-blue-700">
            Run New Analysis
          </Button>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border-green-600">
        <Card.Body className="p-6">
          <div className="flex items-center gap-4">
            <CheckSquare className="w-8 h-8 text-green-400" />
            <div>
              <h3 className="text-xl font-semibold text-green-100 mb-1">
                Personalized Recommendations
              </h3>
              <p className="text-green-200">
                AI-powered suggestions to optimize your path to financial success.
              </p>
            </div>
          </div>

          {/* Progress Summary */}
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{completedCount}</div>
              <div className="text-xs text-gray-400">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{acceptedCount}</div>
              <div className="text-xs text-gray-400">In Progress</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">{pendingCount}</div>
              <div className="text-xs text-gray-400">Pending</div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Filters */}
      <Card className="bg-gray-800">
        <Card.Body className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-white">Filter by Timeline</h4>
            <span className="text-sm text-gray-400">
              {filteredRecommendations.length} recommendations
            </span>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {(['all', 'immediate', 'short_term', 'long_term'] as const).map(filter => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={`
                  px-4 py-2 rounded-lg font-medium text-sm transition-colors
                  ${activeFilter === filter ? 
                    'bg-blue-600 text-white' : 
                    'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'}
                `}
              >
                {filter === 'all' ? 'All' : filter.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                <span className="ml-2 opacity-75">
                  ({filter === 'all' ? 
                    allRecommendations.length : 
                    allRecommendations.filter(r => r.type === filter).length})
                </span>
              </button>
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* Recommendations List */}
      <div className="space-y-4">
        {filteredRecommendations
          .sort((a, b) => {
            // Sort by priority first (high -> medium -> low)
            const priorityOrder = { high: 3, medium: 2, low: 1 };
            const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
            if (priorityDiff !== 0) return priorityDiff;
            
            // Then by type (immediate -> short_term -> long_term)
            const typeOrder = { immediate: 3, short_term: 2, long_term: 1 };
            const typeDiff = typeOrder[b.type] - typeOrder[a.type];
            if (typeDiff !== 0) return typeDiff;
            
            // Finally by success rate improvement
            return b.projected_impact.success_rate_improvement - a.projected_impact.success_rate_improvement;
          })
          .map((recommendation) => (
            <RecommendationCard
              key={recommendation.id}
              recommendation={recommendation}
              onStatusChange={handleStatusChange}
            />
          ))}
      </div>

      {/* Summary Actions */}
      <Card className="bg-gradient-to-r from-indigo-900/20 to-purple-900/20 border-indigo-600">
        <Card.Body className="p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Quick Actions</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" size="sm" className="text-gray-300 hover:text-white">
              <CheckCircle className="w-4 h-4 mr-2" />
              Accept All High Priority
            </Button>
            <Button variant="outline" size="sm" className="text-gray-300 hover:text-white">
              <DollarSign className="w-4 h-4 mr-2" />
              Show Cost-Benefit Analysis
            </Button>
            <Button variant="outline" size="sm" className="text-gray-300 hover:text-white">
              <BarChart3 className="w-4 h-4 mr-2" />
              Export Action Plan
            </Button>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
};