/**
 * WealthPath AI - Comprehensive Projections Page
 * Displays interactive financial projections with editable assumptions
 */
import React, { useState } from 'react';
import { TrendingUp, Calculator, Target, BarChart3, AlertCircle } from 'lucide-react';
import KeyAssumptions from './KeyAssumptions';
import Button from '../ui/Button';
import Card from '../ui/Card';
import { 
  useProjectionQuery, 
  useUpdateAssumptionsMutation, 
  ProjectionAssumptions 
} from '../../hooks/use-projection-queries';

const ProjectionsPage: React.FC = () => {
  const [projectionYears, setProjectionYears] = useState(20);
  const [isRecalculating, setIsRecalculating] = useState(false);

  const { 
    data: projectionData, 
    isLoading: isLoadingProjection, 
    error: projectionError,
    refetch: refetchProjection 
  } = useProjectionQuery({ 
    years: projectionYears, 
    include_monte_carlo: true,
    monte_carlo_iterations: 1000 
  });

  const updateAssumptionsMutation = useUpdateAssumptionsMutation();

  const handleAssumptionsChange = async (assumptions: Record<string, number>) => {
    setIsRecalculating(true);
    try {
      // Convert percentages to decimals for the API
      const apiAssumptions: Partial<ProjectionAssumptions> = {};
      Object.entries(assumptions).forEach(([key, value]) => {
        apiAssumptions[key as keyof ProjectionAssumptions] = value / 100; // Convert percentage to decimal
      });

      await updateAssumptionsMutation.mutateAsync(apiAssumptions);
      
      // Force refetch projections with new assumptions
      await refetchProjection();
    } catch (error) {
      console.error('Failed to update assumptions and recalculate:', error);
    } finally {
      setIsRecalculating(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const confidenceData = projectionData?.monte_carlo_results?.confidence_intervals;
  const projectionYearData = projectionData?.projections?.[projectionYears - 1];

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                <Calculator className="w-8 h-8 text-blue-500" />
                Financial Projections
              </h1>
              <p className="text-lg text-gray-300">
                Comprehensive wealth modeling with Monte Carlo simulation and customizable assumptions
              </p>
            </div>
            <div className="flex items-center gap-3">
              <select
                value={projectionYears}
                onChange={(e) => setProjectionYears(parseInt(e.target.value))}
                className="px-4 py-2 bg-gray-800 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value={10}>10 Years</option>
                <option value={15}>15 Years</option>
                <option value={20}>20 Years</option>
                <option value={25}>25 Years</option>
                <option value={30}>30 Years</option>
              </select>
            </div>
          </div>
        </div>

        {/* Error State */}
        {projectionError && (
          <Card className="mb-6 bg-red-900/20 border-red-600">
            <div className="p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="text-red-300 font-semibold mb-1">Projection Error</h3>
                <p className="text-red-300/80 text-sm">
                  Unable to calculate projections. Please check your financial data and try again.
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Methodology Note */}
        <Card className="mb-6 bg-blue-900/20 border-blue-600">
          <div className="p-4">
            <p className="text-blue-300 text-sm">
              <strong>Methodology:</strong> Multi-factor projection considers asset appreciation, income growth, intelligent savings allocation, and market volatility. 
              Monte Carlo simulation with 1000 iterations provides confidence intervals. Calculation time: {projectionData?.calculation_metadata?.calculation_time_ms || 0}ms.
            </p>
          </div>
        </Card>

        {/* Key Assumptions Section */}
        <div className="mb-8">
          <KeyAssumptions
            onAssumptionsChange={handleAssumptionsChange}
            isLoading={isRecalculating || isLoadingProjection}
          />
        </div>

        {/* Confidence Analysis Results */}
        {confidenceData && (
          <Card className="mb-8 bg-gray-800 border-gray-700">
            <div className="p-6">
              <div className="flex items-center gap-2 mb-6">
                <Target className="w-5 h-5 text-purple-400" />
                <h3 className="text-xl font-semibold text-white">
                  Confidence Analysis (1000 Simulations)
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Conservative Scenario */}
                <div className="bg-orange-900/20 border-2 border-orange-600 rounded-lg p-6 text-center">
                  <div className="text-sm text-orange-300 mb-2">Conservative (90% confident)</div>
                  <div className="text-3xl font-bold text-orange-400 mb-2">
                    {formatCurrency(confidenceData.p10?.[projectionYears - 1] || 0)}
                  </div>
                  <div className="text-xs text-orange-300">
                    90% chance of exceeding this
                  </div>
                </div>

                {/* Expected Scenario */}
                <div className="bg-blue-900/20 border-2 border-blue-600 rounded-lg p-6 text-center">
                  <div className="text-sm text-blue-300 mb-2">Expected (Most Likely)</div>
                  <div className="text-3xl font-bold text-blue-400 mb-2">
                    {formatCurrency(confidenceData.p50?.[projectionYears - 1] || 0)}
                  </div>
                  <div className="text-xs text-blue-300">
                    50% probability
                  </div>
                </div>

                {/* Optimistic Scenario */}
                <div className="bg-green-900/20 border-2 border-green-600 rounded-lg p-6 text-center">
                  <div className="text-sm text-green-300 mb-2">Optimistic (Stretch Goal)</div>
                  <div className="text-3xl font-bold text-green-400 mb-2">
                    {formatCurrency(confidenceData.p90?.[projectionYears - 1] || 0)}
                  </div>
                  <div className="text-xs text-green-300">
                    10% chance of exceeding
                  </div>
                </div>
              </div>

              {/* Additional Details */}
              <div className="mt-6 text-center">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-gray-300 border-gray-600"
                >
                  Show Simulation Details →
                </Button>
              </div>
            </div>
          </Card>
        )}

        {/* Projection Methodology */}
        <Card className="bg-gray-800 border-gray-700">
          <div className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-5 h-5 text-gray-400" />
              <h3 className="text-lg font-semibold text-white">Our Projection Methodology</h3>
              <div className="ml-auto">
                <div className="w-0 h-0 border-l-4 border-r-4 border-t-8 border-transparent border-t-gray-400 cursor-pointer"></div>
              </div>
            </div>
            
            <div className="text-sm text-gray-300 leading-relaxed">
              <p className="mb-3">
                Our advanced projection system uses a multi-factor approach combining your current financial position, 
                income trajectory, spending patterns, and investment allocations. We apply Monte Carlo simulation 
                to model market volatility and provide confidence intervals around our projections.
              </p>
              
              <p className="mb-3">
                <strong>Key Features:</strong> Asset-specific growth rates, inflation adjustment, tax considerations, 
                intelligent rebalancing, and lifecycle-aware allocation shifts. All assumptions are based on 
                historical data and current market conditions, with conservative estimates to ensure reliability.
              </p>

              <p>
                <strong>Confidence Intervals:</strong> Our 1000-iteration Monte Carlo simulation accounts for market 
                volatility, economic cycles, and uncertainty in key variables. This provides you with realistic 
                ranges rather than single-point estimates.
              </p>
            </div>
          </div>
        </Card>

        {/* Loading State */}
        {(isLoadingProjection || isRecalculating) && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="p-8 bg-gray-800 border-gray-700">
              <div className="flex items-center gap-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <div>
                  <div className="text-white font-semibold">
                    {isRecalculating ? 'Recalculating Projections' : 'Loading Projections'}
                  </div>
                  <div className="text-gray-400 text-sm">
                    {isRecalculating 
                      ? 'Applying your new assumptions...' 
                      : 'Running Monte Carlo simulation...'}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectionsPage;