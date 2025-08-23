/**
 * WealthPath AI - Conflicts Tab
 * Shows detected conflicts and resolution options
 */
import React, { useState } from 'react';
import { AlertTriangle, X, Check, Clock, DollarSign, TrendingUp } from 'lucide-react';
import Card from '../../ui/Card';
import Badge from '../../ui/Badge';
import Button from '../../ui/Button';

interface Conflict {
  id: string;
  type: string;
  severity: string;
  description: string;
  affected_goals: string[];
  resolution_options: Array<{
    type: string;
    description: string;
    impact: string;
    [key: string]: any;
  }>;
  shortfall_amount?: number;
}

interface ConflictsTabProps {
  conflicts: Conflict[];
}

const getSeverityColor = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'critical':
      return 'bg-red-900 text-red-200 border-red-600';
    case 'moderate':
      return 'bg-yellow-900 text-yellow-200 border-yellow-600';
    case 'minor':
      return 'bg-blue-900 text-blue-200 border-blue-600';
    default:
      return 'bg-gray-900 text-gray-200 border-gray-600';
  }
};

const getSeverityIcon = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'critical':
      return '🔴';
    case 'moderate':
      return '🟡';
    case 'minor':
      return '🔵';
    default:
      return '⚪';
  }
};

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'cash_flow':
      return <DollarSign className="w-5 h-5" />;
    case 'timeline':
      return <Clock className="w-5 h-5" />;
    case 'risk':
      return <TrendingUp className="w-5 h-5" />;
    default:
      return <AlertTriangle className="w-5 h-5" />;
  }
};

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

interface ConflictCardProps {
  conflict: Conflict;
  onResolve: (conflictId: string, resolutionType: string, params: any) => void;
}

const ConflictCard: React.FC<ConflictCardProps> = ({ conflict, onResolve }) => {
  const [selectedResolution, setSelectedResolution] = useState<string | null>(null);
  const [isResolving, setIsResolving] = useState(false);

  const handleResolve = async () => {
    if (!selectedResolution) return;
    
    setIsResolving(true);
    const resolution = conflict.resolution_options.find(r => r.type === selectedResolution);
    await onResolve(conflict.id, selectedResolution, resolution);
    setIsResolving(false);
  };

  return (
    <Card className={`${getSeverityColor(conflict.severity)} border-2`}>
      <Card.Body className="p-6">
        <div className="flex items-start gap-4">
          {/* Severity Icon */}
          <div className="text-2xl">
            {getSeverityIcon(conflict.severity)}
          </div>
          
          <div className="flex-1">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="text-lg font-semibold uppercase tracking-wide">
                  {conflict.severity}: {conflict.type.replace('_', ' ')}
                </h4>
                <Badge variant="secondary" size="sm" className="mt-1">
                  {conflict.affected_goals.length} goals affected
                </Badge>
              </div>
              <div className="flex items-center gap-1 text-sm opacity-75">
                {getTypeIcon(conflict.type)}
              </div>
            </div>

            {/* Description */}
            <p className="text-lg mb-4">{conflict.description}</p>

            {/* Specific Details */}
            {conflict.shortfall_amount && (
              <div className="bg-black/20 rounded-lg p-3 mb-4">
                <div className="text-sm opacity-90 mb-1">Monthly Shortfall:</div>
                <div className="text-2xl font-bold">{formatCurrency(conflict.shortfall_amount)}</div>
              </div>
            )}

            {/* Resolution Options */}
            <div className="space-y-3 mb-4">
              <h5 className="font-semibold text-sm uppercase tracking-wide opacity-90">
                Resolution Options:
              </h5>
              
              {conflict.resolution_options.map((option, index) => (
                <label key={index} className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name={`resolution-${conflict.id}`}
                    value={option.type}
                    checked={selectedResolution === option.type}
                    onChange={(e) => setSelectedResolution(e.target.value)}
                    className="mt-1 w-4 h-4 text-blue-600"
                  />
                  <div className="flex-1">
                    <div className="font-medium">{option.description}</div>
                    <div className="text-sm opacity-75 mt-1">{option.impact}</div>
                  </div>
                </label>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={handleResolve}
                disabled={!selectedResolution || isResolving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                size="sm"
              >
                <Check className="w-4 h-4 mr-2" />
                {isResolving ? 'Applying...' : 'Apply Selected'}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                className="border-gray-500 text-gray-300 hover:bg-gray-700"
              >
                See Impact Analysis
              </Button>
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export const ConflictsTab: React.FC<ConflictsTabProps> = ({ conflicts }) => {
  const [resolvedConflicts, setResolvedConflicts] = useState<Set<string>>(new Set());

  const handleResolveConflict = async (conflictId: string, resolutionType: string, params: any) => {
    try {
      // Here you would call the API to resolve the conflict
      console.log('Resolving conflict:', conflictId, resolutionType, params);
      
      // For now, just mark as resolved locally
      setResolvedConflicts(prev => new Set([...prev, conflictId]));
      
      // Show success message
      // toast.success('Conflict resolution applied successfully');
    } catch (error) {
      console.error('Failed to resolve conflict:', error);
      // toast.error('Failed to apply resolution');
    }
  };

  const activeConflicts = conflicts.filter(c => !resolvedConflicts.has(c.id));

  if (conflicts.length === 0) {
    return (
      <Card className="text-center py-12">
        <Card.Body>
          <div className="text-6xl mb-4">🎉</div>
          <h3 className="text-2xl font-semibold text-white mb-4">No Conflicts Detected</h3>
          <p className="text-gray-300 mb-6">
            Excellent! Your financial goals are well-aligned and achievable with your current trajectory.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-green-900/20 border border-green-600 rounded-lg p-4">
              <div className="text-green-400 font-semibold mb-2">✅ Cash Flow</div>
              <div className="text-gray-300">Monthly requirements within budget</div>
            </div>
            <div className="bg-green-900/20 border border-green-600 rounded-lg p-4">
              <div className="text-green-400 font-semibold mb-2">✅ Timeline</div>
              <div className="text-gray-300">Goals properly spaced over time</div>
            </div>
            <div className="bg-green-900/20 border border-green-600 rounded-lg p-4">
              <div className="text-green-400 font-semibold mb-2">✅ Risk Alignment</div>
              <div className="text-gray-300">Goals match your risk tolerance</div>
            </div>
          </div>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <Card className="bg-gradient-to-r from-red-900/20 to-orange-900/20 border-red-600">
        <Card.Body className="p-6">
          <div className="flex items-center gap-4">
            <AlertTriangle className="w-8 h-8 text-red-400" />
            <div>
              <h3 className="text-xl font-semibold text-red-100 mb-1">
                {activeConflicts.length} Conflict{activeConflicts.length !== 1 ? 's' : ''} Detected
              </h3>
              <p className="text-red-200">
                These conflicts may prevent you from achieving your goals as planned.
              </p>
            </div>
          </div>
          
          {/* Conflict Breakdown */}
          <div className="mt-4 flex gap-4">
            {['critical', 'moderate', 'minor'].map(severity => {
              const count = activeConflicts.filter(c => c.severity === severity).length;
              if (count === 0) return null;
              
              return (
                <Badge
                  key={severity}
                  variant={severity === 'critical' ? 'error' : 
                          severity === 'moderate' ? 'warning' : 'info'}
                  size="sm"
                >
                  {count} {severity}
                </Badge>
              );
            })}
          </div>
        </Card.Body>
      </Card>

      {/* Resolved Conflicts Summary */}
      {resolvedConflicts.size > 0 && (
        <Card className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border-green-600">
          <Card.Body className="p-4">
            <div className="flex items-center gap-3">
              <Check className="w-6 h-6 text-green-400" />
              <div>
                <h4 className="font-semibold text-green-100">
                  {resolvedConflicts.size} Conflict{resolvedConflicts.size !== 1 ? 's' : ''} Resolved
                </h4>
                <p className="text-sm text-green-200">
                  Solutions have been applied. Re-run analysis to see updated results.
                </p>
              </div>
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Active Conflicts */}
      <div className="space-y-4">
        {activeConflicts
          .sort((a, b) => {
            const severityOrder = { 'critical': 3, 'moderate': 2, 'minor': 1 };
            return severityOrder[b.severity as keyof typeof severityOrder] - 
                   severityOrder[a.severity as keyof typeof severityOrder];
          })
          .map((conflict) => (
            <ConflictCard
              key={conflict.id}
              conflict={conflict}
              onResolve={handleResolveConflict}
            />
          ))}
      </div>

      {/* Action Panel */}
      {activeConflicts.length > 0 && (
        <Card className="bg-gray-800">
          <Card.Body className="p-6">
            <h4 className="text-lg font-semibold text-white mb-4">Quick Actions</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button variant="outline" size="sm" className="text-gray-300 hover:text-white">
                Run Impact Simulation
              </Button>
              <Button variant="outline" size="sm" className="text-gray-300 hover:text-white">
                Export Conflict Report
              </Button>
              <Button variant="outline" size="sm" className="text-gray-300 hover:text-white">
                Schedule Review Meeting
              </Button>
            </div>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};