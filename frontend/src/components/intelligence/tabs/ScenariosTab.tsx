/**
 * WealthPath AI - Scenarios Tab
 * Shows different optimization scenarios with comparison capabilities
 */
import React, { useState } from 'react';
import { 
  GitBranch, 
  TrendingUp, 
  Target, 
  DollarSign, 
  Clock, 
  BarChart3,
  Play,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';
import Card from '../../ui/Card';
import Badge from '../../ui/Badge';
import Button from '../../ui/Button';
import { useMonteCarloSimulation } from '../../../hooks/use-intelligence-hooks';

interface Scenario {
  id: string;
  name: string;
  description: string;
  is_recommended: boolean;
  success_rate: number;
  monthly_requirement_change: number;
  timeline_impact: number;
  required_changes: Array<{
    type: string;
    description: string;
    amount?: number;
  }>;
  projected_outcomes: {
    total_savings: number;
    goal_completion_rate: number;
    risk_score: number;
  };
  monte_carlo_completed: boolean;
}

interface ScenariosTabProps {
  scenarios: Scenario[];
  onScenarioSelect?: (scenarioId: string) => void;
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const normalizeRate = (rate: number): number => {
  // Convert to percentage if it's a decimal (0-1 range)
  return rate <= 1 ? rate * 100 : rate;
};

const getSuccessRateColor = (rate: number): string => {
  const normalized = normalizeRate(rate);
  if (normalized >= 80) return 'text-green-400';
  if (normalized >= 60) return 'text-yellow-400';
  if (normalized >= 40) return 'text-orange-400';
  return 'text-red-400';
};

const getSuccessRateBg = (rate: number): string => {
  const normalized = normalizeRate(rate);
  if (normalized >= 80) return 'from-green-900/30 to-green-800/30 border-green-600';
  if (normalized >= 60) return 'from-yellow-900/30 to-yellow-800/30 border-yellow-600';
  if (normalized >= 40) return 'from-orange-900/30 to-orange-800/30 border-orange-600';
  return 'from-red-900/30 to-red-800/30 border-red-600';
};

interface ScenarioCardProps {
  scenario: Scenario;
  isSelected: boolean;
  onSelect: () => void;
  onRunSimulation: (scenarioId: string) => void;
}

const ScenarioCard: React.FC<ScenarioCardProps> = ({ 
  scenario, 
  isSelected, 
  onSelect,
  onRunSimulation
}) => {
  return (
    <Card 
      className={`
        transition-all duration-300 cursor-pointer
        ${isSelected ? 'border-blue-600 bg-blue-900/20 transform scale-105 shadow-lg' : 'hover:border-gray-600'}
        ${scenario.is_recommended ? 'bg-gradient-to-br from-green-900/10 to-blue-900/10' : ''}
      `}
      onClick={onSelect}
    >
      <Card.Body className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h4 className="text-xl font-semibold text-white">{scenario.name}</h4>
              {scenario.is_recommended && (
                <Badge variant="success" size="sm">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Recommended
                </Badge>
              )}
            </div>
            <p className="text-gray-300 text-sm leading-relaxed">
              {scenario.description}
            </p>
          </div>
          <GitBranch className="w-6 h-6 text-blue-400" />
        </div>

        {/* Success Rate */}
        <div className={`bg-gradient-to-r ${getSuccessRateBg(scenario.success_rate)} border rounded-lg p-4 mb-4`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-300 mb-1">Success Probability</div>
              <div className={`text-3xl font-bold ${getSuccessRateColor(scenario.success_rate)}`}>
                {Math.round(normalizeRate(scenario.success_rate))}%
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-300">Monte Carlo</div>
              <div className="flex items-center gap-2 mt-1">
                {scenario.monte_carlo_completed ? (
                  <Badge variant="success" size="sm">Completed</Badge>
                ) : (
                  <Button 
                    variant="primary"
                    size="sm" 
                    onClick={(e) => {
                      console.log('Run button clicked for scenario:', scenario.id);
                      e.stopPropagation();
                      onRunSimulation(scenario.id);
                    }}
                  >
                    <Play className="w-3 h-3 mr-1" />
                    Run
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-sm text-gray-400 mb-1">Monthly Change</div>
            <div className={`font-semibold ${scenario.monthly_requirement_change > 0 ? 'text-red-400' : 'text-green-400'}`}>
              {scenario.monthly_requirement_change > 0 ? '+' : ''}
              {formatCurrency(scenario.monthly_requirement_change)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-400 mb-1">Timeline Impact</div>
            <div className={`font-semibold ${scenario.timeline_impact > 0 ? 'text-red-400' : 'text-green-400'}`}>
              {scenario.timeline_impact > 0 ? '+' : ''}
              {scenario.timeline_impact} months
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-400 mb-1">Goals Complete</div>
            <div className="text-blue-400 font-semibold">
              {Math.round(scenario.projected_outcomes?.goal_completion_rate || 0)}%
            </div>
          </div>
        </div>

        {/* Required Changes */}
        <div className="space-y-2 mb-4">
          <h5 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
            Required Changes:
          </h5>
          {(scenario.required_changes || []).slice(0, 3).map((change, index) => (
            <div key={index} className="flex items-start gap-2 text-sm">
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
              <div className="text-gray-300">
                {change.description}
                {change.amount && (
                  <span className="text-blue-400 font-medium ml-1">
                    ({formatCurrency(change.amount)})
                  </span>
                )}
              </div>
            </div>
          ))}
          {(scenario.required_changes || []).length > 3 && (
            <div className="text-xs text-gray-400 pl-4">
              +{(scenario.required_changes || []).length - 3} more changes...
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2 mt-4">
          <Button 
            variant={isSelected ? "default" : "outline"}
            size="sm"
            className={isSelected ? "bg-blue-600 hover:bg-blue-700" : ""}
          >
            {isSelected ? 'Selected' : 'Select Scenario'}
          </Button>
          <Button variant="outline" size="sm" className="text-gray-300 hover:text-white">
            View Details
          </Button>
        </div>
      </Card.Body>
    </Card>
  );
};

export const ScenariosTab: React.FC<ScenariosTabProps> = ({ 
  scenarios, 
  onScenarioSelect 
}) => {
  console.log('ScenariosTab - scenarios received:', scenarios);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(
    scenarios.find(s => s.is_recommended)?.id || scenarios[0]?.id || null
  );
  const [simulationResults, setSimulationResults] = useState<Map<string, any>>(new Map());
  
  const monteCarloMutation = useMonteCarloSimulation();

  const handleScenarioSelect = (scenarioId: string) => {
    setSelectedScenario(scenarioId);
    onScenarioSelect?.(scenarioId);
  };

  const handleRunSimulation = async (scenarioId: string) => {
    console.log('Running Monte Carlo simulation for scenario:', scenarioId);
    try {
      const result = await monteCarloMutation.mutateAsync({
        scenario_id: scenarioId,
        iterations: 1000
      });
      
      console.log('Monte Carlo simulation result:', result);
      setSimulationResults(prev => new Map(prev).set(scenarioId, result));
      
      // Update the scenario to mark as completed
      // This will trigger a re-render to show the "Completed" badge
      scenarios.forEach(s => {
        if (s.id === scenarioId) {
          s.monte_carlo_completed = true;
        }
      });
    } catch (error) {
      console.error('Failed to run Monte Carlo simulation:', error);
      // Show error message to user
      alert(`Failed to run simulation: ${error.message || 'Unknown error'}`);
    }
  };

  const selectedScenarioData = scenarios.find(s => s.id === selectedScenario);

  if (scenarios.length === 0) {
    return (
      <Card className="text-center py-12">
        <Card.Body>
          <div className="text-6xl mb-4">🔄</div>
          <h3 className="text-2xl font-semibold text-white mb-4">Generating Scenarios</h3>
          <p className="text-gray-300 mb-6">
            Our AI is analyzing your goals and generating optimization scenarios...
          </p>
          <Button className="bg-blue-600 hover:bg-blue-700">
            Refresh Analysis
          </Button>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-blue-600">
        <Card.Body className="p-6">
          <div className="flex items-center gap-4">
            <GitBranch className="w-8 h-8 text-blue-400" />
            <div>
              <h3 className="text-xl font-semibold text-blue-100 mb-1">
                Optimization Scenarios
              </h3>
              <p className="text-blue-200">
                Compare different paths to achieve your financial goals with varying risk and timeline trade-offs.
              </p>
            </div>
          </div>
          
          <div className="mt-4 flex gap-4">
            <Badge variant="info" size="sm">
              {scenarios.length} scenarios generated
            </Badge>
            <Badge variant="success" size="sm">
              {scenarios.filter(s => s.monte_carlo_completed).length} simulations completed
            </Badge>
          </div>
        </Card.Body>
      </Card>

      {/* Scenario Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {scenarios
          .sort((a, b) => {
            // Recommended scenarios first, then by success rate
            if (a.is_recommended && !b.is_recommended) return -1;
            if (!a.is_recommended && b.is_recommended) return 1;
            return b.success_rate - a.success_rate;
          })
          .map((scenario) => (
            <ScenarioCard
              key={scenario.id}
              scenario={scenario}
              isSelected={selectedScenario === scenario.id}
              onSelect={() => handleScenarioSelect(scenario.id)}
              onRunSimulation={handleRunSimulation}
            />
          ))}
      </div>

      {/* Selected Scenario Details */}
      {selectedScenarioData && (
        <Card className="bg-gray-800">
          <Card.Body className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-400" />
              Selected Scenario: {selectedScenarioData.name}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Projected Savings */}
              <div className="text-center">
                <div className="text-3xl font-bold text-green-400 mb-2">
                  {formatCurrency(selectedScenarioData.projected_outcomes?.total_savings || 0)}
                </div>
                <div className="text-gray-300 font-medium">Total Projected Savings</div>
                <div className="text-sm text-gray-400">By target completion</div>
              </div>
              
              {/* Goal Completion */}
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-400 mb-2">
                  {Math.round(selectedScenarioData.projected_outcomes?.goal_completion_rate || 0)}%
                </div>
                <div className="text-gray-300 font-medium">Goal Completion</div>
                <div className="text-sm text-gray-400">Expected achievement rate</div>
              </div>
              
              {/* Risk Score */}
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-400 mb-2">
                  {Math.round(selectedScenarioData.projected_outcomes?.risk_score || 7)}/10
                </div>
                <div className="text-gray-300 font-medium">Risk Score</div>
                <div className="text-sm text-gray-400">Portfolio risk level</div>
              </div>
              
              {/* Success Rate */}
              <div className="text-center">
                <div className={`text-3xl font-bold mb-2 ${getSuccessRateColor(selectedScenarioData.success_rate)}`}>
                  {Math.round(normalizeRate(selectedScenarioData.success_rate))}%
                </div>
                <div className="text-gray-300 font-medium">Success Probability</div>
                <div className="text-sm text-gray-400">Monte Carlo result</div>
              </div>
            </div>

            {/* All Required Changes */}
            <div className="mt-6 pt-6 border-t border-gray-700">
              <h4 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-400" />
                Implementation Steps
              </h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(selectedScenarioData.required_changes || []).map((change, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-gray-700/50 rounded-lg">
                    <div className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">
                      {index + 1}
                    </div>
                    <div>
                      <div className="text-white font-medium">{(change.type || 'general').replace('_', ' ').toUpperCase()}</div>
                      <div className="text-gray-300 text-sm">{change.description}</div>
                      {change.amount && (
                        <div className="text-blue-400 text-sm font-medium mt-1">
                          Impact: {formatCurrency(change.amount)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex gap-4">
              <Button className="bg-blue-600 hover:bg-blue-700">
                <CheckCircle className="w-4 h-4 mr-2" />
                Apply This Scenario
              </Button>
              <Button variant="outline" className="text-gray-300 hover:text-white">
                <BarChart3 className="w-4 h-4 mr-2" />
                Compare All Scenarios
              </Button>
              <Button variant="outline" className="text-gray-300 hover:text-white">
                <Clock className="w-4 h-4 mr-2" />
                View Timeline Impact
              </Button>
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Performance Note */}
      <Card className="bg-gradient-to-r from-yellow-900/20 to-orange-900/20 border-yellow-600">
        <Card.Body className="p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-yellow-100 font-semibold mb-1">Scenario Performance Notes</h4>
              <p className="text-yellow-200 text-sm">
                Success rates are based on Monte Carlo simulations with 1,000 iterations. 
                Scenarios consider market volatility, inflation, and your risk tolerance. 
                Higher success rates may require more aggressive savings or longer timelines.
              </p>
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
};