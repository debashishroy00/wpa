/**
 * WealthPath AI - Financial Summary Dashboard Component
 */
import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  PieChart, 
  Activity,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Info,
} from 'lucide-react';
import { format } from 'date-fns';

import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { DataQuality } from '../../types/financial';
import { 
  useFinancialSummaryQuery,
  useDataQualityQuery,
  useTriggerDataSyncMutation,
  useCreateNetWorthSnapshotMutation,
} from '../../hooks/use-financial-queries';

const FinancialSummaryDashboard: React.FC = () => {
  const { data: summary, isLoading: summaryLoading, refetch: refetchSummary } = useFinancialSummaryQuery();
  const { data: dataQuality, isLoading: dqLoading } = useDataQualityQuery();
  const triggerSyncMutation = useTriggerDataSyncMutation();
  const createSnapshotMutation = useCreateNetWorthSnapshotMutation();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getDataQualityColor = (dq: DataQuality) => {
    switch (dq) {
      case DataQuality.DQ1:
        return 'text-green-600';
      case DataQuality.DQ2:
        return 'text-blue-600';
      case DataQuality.DQ3:
        return 'text-yellow-600';
      case DataQuality.DQ4:
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getDataQualityIcon = (dq: DataQuality) => {
    switch (dq) {
      case DataQuality.DQ1:
        return <CheckCircle className="w-4 h-4" />;
      case DataQuality.DQ2:
        return <Info className="w-4 h-4" />;
      case DataQuality.DQ3:
        return <AlertTriangle className="w-4 h-4" />;
      case DataQuality.DQ4:
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const handleRefreshData = async () => {
    try {
      await triggerSyncMutation.mutateAsync();
      // Refetch summary after sync
      setTimeout(() => {
        refetchSummary();
      }, 3000);
    } catch (error) {
      console.error('Failed to trigger data sync:', error);
    }
  };

  const handleCreateSnapshot = async () => {
    try {
      await createSnapshotMutation.mutateAsync();
    } catch (error) {
      console.error('Failed to create snapshot:', error);
    }
  };

  if (summaryLoading && !summary) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <Card.Body>
                <div className="h-20 bg-gray-700 rounded"></div>
              </Card.Body>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <Card>
        <Card.Body className="text-center py-6">
          <p className="text-gray-300">No financial data available</p>
          <p className="text-sm text-gray-400 mt-1">
            Start by adding your financial entries to see your summary
          </p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Financial Summary</h2>
          <p className="text-sm text-gray-600 mt-1">
            Last updated: {format(new Date(summary.last_updated), 'PPpp')}
          </p>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshData}
            isLoading={triggerSyncMutation.isLoading}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Sync Data
          </Button>
          <Button
            size="sm"
            onClick={handleCreateSnapshot}
            isLoading={createSnapshotMutation.isLoading}
            leftIcon={<Activity className="w-4 h-4" />}
          >
            Create Snapshot
          </Button>
        </div>
      </div>

      {/* Main Financial Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Net Worth */}
        <Card className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full transform translate-x-8 -translate-y-8 opacity-10"></div>
          <div className="relative">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-blue-100 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-600" />
              </div>
              <div className={`flex items-center space-x-1 ${getDataQualityColor(summary.data_quality_score)}`}>
                {getDataQualityIcon(summary.data_quality_score)}
                <Badge variant="info" size="sm">
                  {summary.data_quality_score}
                </Badge>
              </div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Net Worth</h3>
            <p className={`text-2xl font-bold ${summary.net_worth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(summary.net_worth)}
            </p>
            {summary.net_worth_change && (
              <div className={`flex items-center mt-1 text-sm ${
                summary.net_worth_change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {summary.net_worth_change >= 0 ? (
                  <TrendingUp className="w-4 h-4 mr-1" />
                ) : (
                  <TrendingDown className="w-4 h-4 mr-1" />
                )}
                {formatCurrency(Math.abs(summary.net_worth_change))}
                {summary.net_worth_change_percentage && (
                  <span className="ml-1">
                    ({summary.net_worth_change_percentage.toFixed(1)}%)
                  </span>
                )}
              </div>
            )}
          </div>
        </Card>

        {/* Total Assets */}
        <Card className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-green-500 to-green-600 rounded-full transform translate-x-8 -translate-y-8 opacity-10"></div>
          <div className="relative">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Total Assets</h3>
            <p className="text-2xl font-bold text-green-600">
              {formatCurrency(summary.total_assets)}
            </p>
            <div className="flex items-center justify-between mt-2 text-sm text-gray-600">
              <span>Liquid: {formatCurrency(summary.liquid_assets || 0)}</span>
              <span>Invested: {formatCurrency(summary.investment_assets || 0)}</span>
            </div>
          </div>
        </Card>

        {/* Total Liabilities */}
        <Card className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-br from-red-500 to-red-600 rounded-full transform translate-x-8 -translate-y-8 opacity-10"></div>
          <div className="relative">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-red-100 rounded-lg">
                <TrendingDown className="w-5 h-5 text-red-600" />
              </div>
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Total Liabilities</h3>
            <p className="text-2xl font-bold text-red-600">
              {formatCurrency(summary.total_liabilities)}
            </p>
            <div className="flex items-center justify-between mt-2 text-sm text-gray-600">
              <span>Debt-to-Asset: {((summary.total_liabilities / summary.total_assets) * 100).toFixed(1)}%</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Asset Breakdown */}
      {(summary.liquid_assets || summary.investment_assets || summary.real_estate_assets || summary.other_assets) && (
        <Card>
          <Card.Header>
            <Card.Title>Asset Breakdown</Card.Title>
          </Card.Header>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {summary.liquid_assets > 0 && (
              <div className="text-center">
                <div className="p-3 bg-blue-50 rounded-lg mb-2">
                  <DollarSign className="w-6 h-6 text-blue-600 mx-auto" />
                </div>
                <p className="text-sm font-medium text-gray-900">Liquid Assets</p>
                <p className="text-lg font-semibold text-blue-600">
                  {formatCurrency(summary.liquid_assets)}
                </p>
                <p className="text-xs text-gray-500">
                  {((summary.liquid_assets / summary.total_assets) * 100).toFixed(1)}%
                </p>
              </div>
            )}
            
            {summary.investment_assets > 0 && (
              <div className="text-center">
                <div className="p-3 bg-green-50 rounded-lg mb-2">
                  <TrendingUp className="w-6 h-6 text-green-600 mx-auto" />
                </div>
                <p className="text-sm font-medium text-gray-900">Investments</p>
                <p className="text-lg font-semibold text-green-600">
                  {formatCurrency(summary.investment_assets)}
                </p>
                <p className="text-xs text-gray-500">
                  {((summary.investment_assets / summary.total_assets) * 100).toFixed(1)}%
                </p>
              </div>
            )}
            
            {summary.real_estate_assets > 0 && (
              <div className="text-center">
                <div className="p-3 bg-yellow-50 rounded-lg mb-2">
                  <PieChart className="w-6 h-6 text-yellow-600 mx-auto" />
                </div>
                <p className="text-sm font-medium text-gray-900">Real Estate</p>
                <p className="text-lg font-semibold text-yellow-600">
                  {formatCurrency(summary.real_estate_assets)}
                </p>
                <p className="text-xs text-gray-500">
                  {((summary.real_estate_assets / summary.total_assets) * 100).toFixed(1)}%
                </p>
              </div>
            )}
            
            {summary.other_assets > 0 && (
              <div className="text-center">
                <div className="p-3 bg-gray-50 rounded-lg mb-2">
                  <PieChart className="w-6 h-6 text-gray-600 mx-auto" />
                </div>
                <p className="text-sm font-medium text-gray-900">Other Assets</p>
                <p className="text-lg font-semibold text-gray-600">
                  {formatCurrency(summary.other_assets)}
                </p>
                <p className="text-xs text-gray-500">
                  {((summary.other_assets / summary.total_assets) * 100).toFixed(1)}%
                </p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Data Quality Insights */}
      {dataQuality && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="hover:border-blue-600 transition-colors">
            <Card.Body className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Data Quality Overview</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Overall Quality</span>
                  <Badge 
                    variant={dataQuality.overall_score === DataQuality.DQ1 ? 'success' : 
                            dataQuality.overall_score === DataQuality.DQ2 ? 'info' : 
                            dataQuality.overall_score === DataQuality.DQ3 ? 'warning' : 'default'}
                  >
                    {dataQuality.overall_score}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Total Entries</span>
                  <span className="font-medium text-white">{dataQuality.total_entries}</span>
                </div>
                <div className="space-y-2">
                  {Object.entries(dataQuality.data_quality_breakdown).map(([dq, count]) => (
                    count > 0 && (
                      <div key={dq} className="flex items-center justify-between text-sm">
                        <span className="text-gray-300">{dq}</span>
                        <span className="text-white">{count}</span>
                      </div>
                    )
                  ))}
                </div>
              </div>
            </Card.Body>
          </Card>

          <Card className="hover:border-blue-600 transition-colors">
            <Card.Body className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Account Summary</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Connected Accounts</span>
                  <span className="font-medium text-white">{summary.connected_accounts}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Manual Entries</span>
                  <span className="font-medium text-white">{summary.manual_entries}</span>
                </div>
                <div className="text-xs text-gray-400 mt-2">
                  Higher connected account ratios improve data quality automatically
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>
      )}

      {/* Recommendations */}
      {dataQuality?.recommendations && dataQuality.recommendations.length > 0 && (
        <Card className="hover:border-blue-600 transition-colors">
          <Card.Body className="p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Recommendations</h3>
            <div className="space-y-2">
              {dataQuality.recommendations.filter(Boolean).map((recommendation, index) => (
                <div key={index} className="flex items-start space-x-2 text-sm">
                  <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-300">{recommendation}</span>
                </div>
              ))}
            </div>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default FinancialSummaryDashboard;