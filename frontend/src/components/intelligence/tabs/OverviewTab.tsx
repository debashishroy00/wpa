/**
 * WealthPath AI - Intelligence Overview Tab
 * Shows comprehensive overview of goals and combined requirements
 */
import React from 'react';
import { TrendingUp, AlertTriangle, CheckCircle, Target, DollarSign } from 'lucide-react';
import Card from '../../ui/Card';
import Badge from '../../ui/Badge';
import Button from '../../ui/Button';

interface Goal {
  goal_id: string;
  name: string;
  category: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  feasibility_score: number;
  monthly_required: number;
  risk_aligned: boolean;
}

interface OverviewTabProps {
  analysis: {
    goals: Goal[];
    gaps: {
      monthly_shortfall: number;
      total_capital_needed: number;
      current_trajectory: number;
      gap_amount: number;
    };
    scenarios: any[];
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

const getFeasibilityColor = (score: number): string => {
  if (score >= 80) return 'text-green-500 bg-green-500';
  if (score >= 60) return 'text-yellow-500 bg-yellow-500';
  if (score >= 40) return 'text-orange-500 bg-orange-500';
  return 'text-red-500 bg-red-500';
};

const getFeasibilityBars = (score: number): string => {
  const bars = Math.ceil(score / 20);
  return '█'.repeat(bars) + '░'.repeat(5 - bars);
};

export const OverviewTab: React.FC<OverviewTabProps> = ({ analysis }) => {
  const { goals = [], gaps = {}, scenarios = [] } = analysis || {};
  
  const totalMonthlyRequired = goals.reduce((sum, goal) => sum + (goal.monthly_required || 0), 0);
  const totalAvailable = totalMonthlyRequired - (gaps.monthly_shortfall || 0);
  
  const recommendedScenario = scenarios.find(s => s && s.is_recommended);

  return (
    <div className="space-y-6">
      {/* Goals Overview Table */}
      <Card className="hover:border-blue-600 transition-colors">
        <Card.Body className="p-6">
          <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-400" />
            Goals Overview
          </h3>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left text-gray-300 font-medium py-3 px-2">Goal</th>
                  <th className="text-right text-gray-300 font-medium py-3 px-2">Target</th>
                  <th className="text-right text-gray-300 font-medium py-3 px-2">Required/Month</th>
                  <th className="text-center text-gray-300 font-medium py-3 px-2">Feasibility</th>
                  <th className="text-center text-gray-300 font-medium py-3 px-2">Risk</th>
                </tr>
              </thead>
              <tbody>
                {goals.map((goal) => (
                  <tr key={goal.goal_id} className="border-b border-gray-800 hover:bg-gray-800/50">
                    <td className="py-4 px-2">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{getCategoryEmoji(goal.category)}</span>
                        <div>
                          <div className="text-white font-medium">{goal.name}</div>
                          <div className="text-sm text-gray-400 capitalize">
                            {goal.category.replace('_', ' ')}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="text-right py-4 px-2">
                      <div className="text-white font-medium">{formatCurrency(goal.target_amount)}</div>
                    </td>
                    <td className="text-right py-4 px-2">
                      <div className="text-white font-medium">{formatCurrency(goal.monthly_required)}</div>
                    </td>
                    <td className="text-center py-4 px-2">
                      <div className="flex flex-col items-center">
                        <div className={`text-sm font-mono ${getFeasibilityColor(goal.feasibility_score).split(' ')[0]}`}>
                          {getFeasibilityBars(goal.feasibility_score)}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {Math.round(goal.feasibility_score)}%
                        </div>
                      </div>
                    </td>
                    <td className="text-center py-4 px-2">
                      {goal.risk_aligned ? (
                        <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-yellow-500 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card.Body>
      </Card>

      {/* Combined Requirements Summary */}
      <Card className="hover:border-blue-600 transition-colors">
        <Card.Body className="p-6">
          <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-green-400" />
            Combined Requirements
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Monthly Requirements */}
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400 mb-2">
                {formatCurrency(totalMonthlyRequired)}
              </div>
              <div className="text-gray-300 font-medium">Total Monthly Need</div>
              <div className="text-sm text-gray-400">Across all goals</div>
            </div>
            
            {/* Available Funds */}
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400 mb-2">
                {formatCurrency(totalAvailable)}
              </div>
              <div className="text-gray-300 font-medium">Available</div>
              <div className="text-sm text-gray-400">Current capacity</div>
            </div>
            
            {/* Gap */}
            <div className="text-center">
              <div className={`text-3xl font-bold mb-2 ${(gaps.monthly_shortfall || 0) > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {(gaps.monthly_shortfall || 0) > 0 ? 
                  `-${formatCurrency(gaps.monthly_shortfall || 0)}` : 
                  `+${formatCurrency(Math.abs(gaps.monthly_shortfall || 0))}`
                }
                {(gaps.monthly_shortfall || 0) > 0 && <span className="ml-2">❌</span>}
                {(gaps.monthly_shortfall || 0) <= 0 && <span className="ml-2">✅</span>}
              </div>
              <div className="text-gray-300 font-medium">
                {(gaps.monthly_shortfall || 0) > 0 ? 'Gap' : 'Surplus'}
              </div>
              <div className="text-sm text-gray-400">
                {(gaps.monthly_shortfall || 0) > 0 ? 'Monthly shortfall' : 'Monthly surplus'}
              </div>
            </div>
          </div>

          {/* Action Button */}
          {(gaps.monthly_shortfall || 0) > 0 && (
            <div className="mt-6 text-center">
              <Button className="bg-blue-600 hover:bg-blue-700">
                <TrendingUp className="w-4 h-4 mr-2" />
                View Optimization Options →
              </Button>
            </div>
          )}

          {/* Quick Stats */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{goals.length}</div>
                <div className="text-gray-400">Active Goals</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {goals.filter(g => g && (g.feasibility_score || 0) >= 80).length}
                </div>
                <div className="text-gray-400">High Feasibility</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-400">
                  {goals.filter(g => g && !g.risk_aligned).length}
                </div>
                <div className="text-gray-400">Risk Misaligned</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">
                  {formatCurrency(gaps.total_capital_needed || 0).replace('$', '').replace(',', '')}k
                </div>
                <div className="text-gray-400">Total Target</div>
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Recommended Path Teaser */}
      {recommendedScenario && (
        <Card className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border-green-600">
          <Card.Body className="p-6">
            <div className="flex items-start gap-4">
              <div className="bg-green-600 rounded-full p-2">
                <CheckCircle className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-green-100 mb-2">
                  Recommended Optimization Path Available
                </h4>
                <p className="text-green-200 mb-3">
                  {recommendedScenario.name}: {Math.round(recommendedScenario.success_rate <= 1 ? recommendedScenario.success_rate * 100 : recommendedScenario.success_rate)}% success probability
                </p>
                <p className="text-sm text-green-300 mb-4">
                  Our analysis suggests specific optimizations that could improve your goal achievement probability.
                </p>
                <Button variant="outline" size="sm" className="border-green-500 text-green-400 hover:bg-green-600 hover:text-white">
                  View Scenarios Tab →
                </Button>
              </div>
            </div>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};