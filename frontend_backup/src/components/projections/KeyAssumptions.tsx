/**
 * WealthPath AI - Interactive Key Assumptions Component
 * Allows users to adjust projection assumptions with sliders and see immediate visual feedback
 */
import React, { useState, useEffect } from 'react';
import { Settings, TrendingUp, Home, BarChart3, DollarSign, AlertTriangle } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';

interface AssumptionConfig {
  key: string;
  label: string;
  icon: React.ComponentType<{className?: string}>;
  min: number;
  max: number;
  step: number;
  color: string;
  description: string;
  defaultValue: number;
}

interface KeyAssumptionsProps {
  onAssumptionsChange?: (assumptions: Record<string, number>) => void;
  isLoading?: boolean;
}

const KeyAssumptions: React.FC<KeyAssumptionsProps> = ({
  onAssumptionsChange,
  isLoading = false
}) => {
  const [assumptions, setAssumptions] = useState({
    salary_growth_rate: 2.0,
    real_estate_appreciation: 2.5,
    stock_market_return: 5.0,
    retirement_account_return: 6.5,
    inflation_rate: 2.5
  });
  
  const [hasChanges, setHasChanges] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  const assumptionConfigs: AssumptionConfig[] = [
    {
      key: 'salary_growth_rate',
      label: 'Salary Growth',
      icon: DollarSign,
      min: 0,
      max: 10,
      step: 0.5,
      color: 'text-green-400',
      description: 'Industry average for your role and experience',
      defaultValue: 2.0
    },
    {
      key: 'real_estate_appreciation',
      label: 'Real Estate',
      icon: Home,
      min: 0,
      max: 8,
      step: 0.5,
      color: 'text-green-400',
      description: 'Based on your property locations and market data',
      defaultValue: 2.5
    },
    {
      key: 'stock_market_return',
      label: 'Stock Returns',
      icon: TrendingUp,
      min: 0,
      max: 15,
      step: 0.5,
      color: 'text-green-400',
      description: 'Historical S&P 500 average: 10%, we use conservative 8%',
      defaultValue: 5.0
    },
    {
      key: 'retirement_account_return',
      label: '401k Return',
      icon: BarChart3,
      min: 0,
      max: 12,
      step: 0.5,
      color: 'text-green-400',
      description: 'Conservative retirement account growth rate',
      defaultValue: 6.5
    },
    {
      key: 'inflation_rate',
      label: 'Inflation',
      icon: BarChart3,
      min: 0,
      max: 6,
      step: 0.5,
      color: 'text-green-400',
      description: 'Federal Reserve target + 0.5% buffer',
      defaultValue: 2.5
    }
  ];

  const handleSliderChange = (key: string, value: number) => {
    setAssumptions(prev => ({
      ...prev,
      [key]: value
    }));
    setHasChanges(true);
  };

  const handleApplyChanges = async () => {
    if (!hasChanges || !onAssumptionsChange) return;

    setIsApplying(true);
    try {
      await onAssumptionsChange(assumptions);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to apply assumption changes:', error);
    } finally {
      setIsApplying(false);
    }
  };

  const resetToDefaults = () => {
    const defaultAssumptions = assumptionConfigs.reduce((acc, config) => ({
      ...acc,
      [config.key]: config.defaultValue
    }), {});
    
    setAssumptions(defaultAssumptions);
    setHasChanges(true);
  };

  return (
    <Card className="bg-gray-800 border-gray-700">
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Key Assumptions Used
          </h3>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={resetToDefaults}
              disabled={isLoading}
              className="text-gray-300 border-gray-600 hover:bg-gray-700"
            >
              Reset Defaults
            </Button>
            {hasChanges && (
              <Button
                onClick={handleApplyChanges}
                disabled={isApplying || isLoading}
                className={`px-6 py-2 font-medium transition-all ${
                  isApplying 
                    ? 'bg-gray-600' 
                    : 'bg-blue-600 hover:bg-blue-700 animate-pulse shadow-lg shadow-blue-500/20'
                }`}
              >
                {isApplying ? 'Applying...' : 'Apply Changes & Recalculate'}
              </Button>
            )}
          </div>
        </div>

        {/* Assumptions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          {assumptionConfigs.map((config) => {
            const Icon = config.icon;
            const currentValue = assumptions[config.key] || config.defaultValue;
            const isChanged = currentValue !== config.defaultValue;
            
            return (
              <div 
                key={config.key} 
                className={`bg-gray-700 rounded-lg p-4 transition-all duration-200 ${
                  isChanged ? 'ring-2 ring-blue-500 bg-gray-700/80' : ''
                }`}
              >
                {/* Category Header */}
                <div className="flex items-center gap-2 mb-3">
                  <Icon className={`w-4 h-4 ${config.color}`} />
                  <span className="text-sm text-gray-300 font-medium">{config.label}</span>
                  {isChanged && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  )}
                </div>

                {/* Current Value Display */}
                <div className={`text-2xl font-bold mb-4 transition-colors ${
                  isChanged ? 'text-blue-400' : config.color
                }`}>
                  {currentValue.toFixed(1)}%
                </div>

                {/* Slider */}
                <div className="mb-3">
                  <input
                    type="range"
                    min={config.min}
                    max={config.max}
                    step={config.step}
                    value={currentValue}
                    onChange={(e) => handleSliderChange(config.key, parseFloat(e.target.value))}
                    disabled={isLoading}
                    className={`w-full h-2 rounded-lg appearance-none cursor-pointer transition-all ${
                      isLoading ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                    style={{
                      background: `linear-gradient(to right, #4f46e5 0%, #4f46e5 ${((currentValue - config.min) / (config.max - config.min)) * 100}%, #374151 ${((currentValue - config.min) / (config.max - config.min)) * 100}%, #374151 100%)`
                    }}
                  />
                </div>

                {/* Min/Max Labels */}
                <div className="flex justify-between text-xs text-gray-500 mb-2">
                  <span>{config.min}%</span>
                  <span>{config.max}%</span>
                </div>

                {/* Description */}
                <div className="text-xs text-gray-400 leading-tight">
                  {config.description}
                </div>

                {/* Default Value Indicator */}
                {isChanged && (
                  <div className="text-xs text-blue-400 mt-2 font-medium">
                    Default: {config.defaultValue}%
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Warning Message */}
        {hasChanges && (
          <div className="flex items-start gap-3 p-4 bg-orange-900/30 border border-orange-600 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-orange-300 font-medium mb-1">
                Projection Parameters Modified
              </p>
              <p className="text-sm text-orange-300/80">
                Adjusting these assumptions will recalculate all projections and confidence intervals. 
                Click "Apply Changes" to see updated results with your custom parameters.
              </p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="flex items-center gap-3 text-gray-400">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              <span>Recalculating projections with new assumptions...</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default KeyAssumptions;