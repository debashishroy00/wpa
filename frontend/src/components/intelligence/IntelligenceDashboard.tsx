/**
 * WealthPath AI - Intelligence Analysis Dashboard
 * Main component for Step 4 Intelligence Analysis
 */
import React, { useState, useEffect } from 'react';
import { 
  Target,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Calendar,
  Users,
  Zap
} from 'lucide-react';

import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { ScoreCard } from './components/ScoreCard';
import { MetricsBar } from './components/MetricsBar';
import { TabNavigation } from './components/TabNavigation';
import { OverviewTab } from './tabs/OverviewTab';
import { ConflictsTab } from './tabs/ConflictsTab';
import { ScenariosTab } from './tabs/ScenariosTab';
import { TimelineTab } from './tabs/TimelineTab';
import { RecommendationsTab } from './tabs/RecommendationsTab';
import { useIntelligenceAnalysis, useRunAnalysisMutation } from '../../hooks/use-intelligence-hooks';

interface IntelligenceDashboardProps {
  onNext?: () => void;
  className?: string;
}

export type TabType = 'overview' | 'conflicts' | 'scenarios' | 'timeline' | 'recommendations';

interface IntelligenceAnalysis {
  analysis_id: string;
  timestamp: string;
  overall_score: number;
  success_probability: number;
  goals: any[];
  gaps: {
    monthly_shortfall: number;
    total_capital_needed: number;
    current_trajectory: number;
    gap_amount: number;
  };
  conflicts: any[];
  scenarios: any[];
  recommendations: {
    immediate: any[];
    short_term: any[];
    long_term: any[];
  };
}

const IntelligenceDashboard: React.FC<IntelligenceDashboardProps> = ({ onNext, className = '' }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  
  const { 
    data: analysis, 
    isLoading, 
    error, 
    refetch 
  } = useIntelligenceAnalysis();

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
  };

  const handleRunAnalysis = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-300">Analyzing your financial goals...</p>
              <p className="text-sm text-gray-400 mt-2">Running Monte Carlo simulations and conflict detection</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Card className="text-center py-8">
            <Card.Body>
              <AlertTriangle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Analysis Failed</h3>
              <p className="text-gray-300 mb-6">
                Unable to analyze your goals. Please ensure you have completed Steps 2 and 3.
              </p>
              <div className="flex gap-4 justify-center">
                <Button onClick={handleRunAnalysis} className="bg-blue-600 hover:bg-blue-700">
                  Retry Analysis
                </Button>
                <Button variant="outline" onClick={() => window.location.href = '/goals'}>
                  Check Goals Setup
                </Button>
              </div>
            </Card.Body>
          </Card>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-gray-900 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Card className="text-center py-12">
            <Card.Body>
              <Target className="w-16 h-16 text-blue-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No Analysis Available</h3>
              <p className="text-gray-300 mb-6">
                Run your first intelligence analysis to get personalized insights and recommendations.
              </p>
              <Button onClick={handleRunAnalysis} className="bg-blue-600 hover:bg-blue-700">
                <Zap className="w-4 h-4 mr-2" />
                Run Intelligence Analysis
              </Button>
            </Card.Body>
          </Card>
        </div>
      </div>
    );
  }

  const getScoreMessage = (score: number): string => {
    if (score >= 80) return "Excellent probability - Goals are well-aligned";
    if (score >= 60) return "Good probability - Minor optimizations recommended";
    if (score >= 40) return "Moderate probability - Optimization recommended";
    return "Challenging - Significant adjustments needed";
  };

  const getScoreTrend = (score: number): 'up' | 'down' | 'stable' => {
    // In a real implementation, this would compare with previous analysis
    return score >= 70 ? 'up' : score >= 50 ? 'stable' : 'down';
  };

  const calculateMetrics = (analysis: IntelligenceAnalysis) => {
    const monthlyGap = analysis.gaps?.monthly_shortfall || 0;
    const successRate = analysis.success_probability ? Math.round(analysis.success_probability * 100) : 85;
    
    // Calculate risk alignment (simplified)
    const riskAlign = analysis.conflicts?.length === 0 ? 95 : 
                     analysis.conflicts?.length === 1 ? 75 : 
                     60;
    
    // Calculate lifestyle fit based on required changes
    const lifestyleFit = analysis.scenarios?.find(s => s.is_recommended)?.lifestyle_impact * 100 || 85;

    return {
      monthlyGap,
      successRate,
      riskAlign: Math.round(riskAlign),
      lifestyleFit: Math.round(lifestyleFit)
    };
  };

  const metrics = calculateMetrics(analysis);

  return (
    <div className={`min-h-screen bg-gray-900 py-8 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <BarChart3 className="w-8 h-8 text-purple-500" />
                Intelligence Analysis
              </h1>
              <p className="text-gray-300 mt-1">Comprehensive goal analysis and optimization recommendations</p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={handleRunAnalysis}
                className="flex items-center gap-2"
              >
                <TrendingUp className="w-4 h-4" />
                Refresh Analysis
              </Button>
              {onNext && (
                <Button
                  onClick={onNext}
                  className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
                >
                  Continue to Action Plan →
                </Button>
              )}
            </div>
          </div>

          {/* Analysis Timestamp */}
          <div className="text-sm text-gray-400">
            Last updated: {analysis.timestamp ? new Date(analysis.timestamp).toLocaleString() : 'Now'}
          </div>
        </div>

        {/* Score Card */}
        <div className="mb-8">
          <ScoreCard 
            score={analysis.overall_score || 75}
            trend={getScoreTrend(analysis.overall_score || 75)}
            message={getScoreMessage(analysis.overall_score || 75)}
          />
        </div>

        {/* Metrics Bar */}
        <div className="mb-8">
          <MetricsBar 
            monthlyGap={metrics.monthlyGap}
            successRate={metrics.successRate}
            riskAlign={metrics.riskAlign}
            lifestyleFit={metrics.lifestyleFit}
          />
        </div>

        {/* Tab Navigation */}
        <div className="mb-6">
          <TabNavigation 
            activeTab={activeTab}
            onTabChange={handleTabChange}
            conflictCount={analysis.conflicts?.length || 0}
            scenarioCount={analysis.scenarios?.length || 0}
            recommendationCount={
              (analysis.recommendations?.immediate?.length || 0) + 
              (analysis.recommendations?.short_term?.length || 0) + 
              (analysis.recommendations?.long_term?.length || 0)
            }
          />
        </div>

        {/* Tab Content */}
        <div className="mb-8">
          {activeTab === 'overview' && <OverviewTab analysis={analysis} />}
          {activeTab === 'conflicts' && <ConflictsTab conflicts={analysis.conflicts || []} />}
          {activeTab === 'scenarios' && (
            <ScenariosTab 
              scenarios={analysis.scenarios || []}
              onScenarioSelect={setSelectedScenario}
            />
          )}
          {activeTab === 'timeline' && (
            <TimelineTab 
              timeline={{
                goals: (analysis.goals || []).map(goal => ({
                  goal_id: goal.goal_id,
                  name: goal.name,
                  category: goal.category,
                  target_date: goal.target_date,
                  current_amount: goal.current_amount,
                  target_amount: goal.target_amount,
                  monthly_required: goal.monthly_required,
                  feasibility_score: goal.feasibility_score,
                  milestones: goal.milestones || [],
                  status: goal.feasibility_score >= 80 ? 'on_track' : 
                          goal.feasibility_score >= 60 ? 'at_risk' : 'behind'
                })),
                major_milestones: []
              }}
            />
          )}
          {activeTab === 'recommendations' && (
            <RecommendationsTab 
              recommendations={analysis.recommendations || { immediate: [], short_term: [], long_term: [] }}
            />
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center">
          <div className="flex gap-3">
            <Button variant="outline" size="sm">
              <Users className="w-4 h-4 mr-2" />
              Share Analysis
            </Button>
            <Button variant="outline" size="sm">
              <Calendar className="w-4 h-4 mr-2" />
              Schedule Review
            </Button>
          </div>
          
          {onNext && (
            <Button
              onClick={onNext}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Continue to Action Plan →
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default IntelligenceDashboard;