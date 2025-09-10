import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Trash2, Calendar, DollarSign } from 'lucide-react';
import { snapshotApi } from '../services/snapshotApi';
import { Snapshot, TimelineData, DetailedSnapshot } from '../types/snapshot';

interface SnapshotTimelineProps {
  refreshTrigger?: number;
}

const SnapshotTimeline: React.FC<SnapshotTimelineProps> = ({ refreshTrigger }) => {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [detailedSnapshots, setDetailedSnapshots] = useState<DetailedSnapshot[]>([]);
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'chart' | 'table'>('chart');
  const [period, setPeriod] = useState<'all' | 'monthly' | 'quarterly' | 'yearly'>('all');

  useEffect(() => {
    fetchData();
  }, [refreshTrigger, period]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const periodParam = period === 'all' ? undefined : period;
      const [snapshotsData, detailedData, chartData] = await Promise.all([
        snapshotApi.getSnapshots(period === 'all' ? 50 : 100, periodParam),
        snapshotApi.getDetailedSnapshots(4, periodParam),
        snapshotApi.getTimelineData(periodParam)
      ]);
      
      setSnapshots(snapshotsData);
      setDetailedSnapshots(detailedData);
      setTimelineData(chartData);
    } catch (error) {
      console.error('Failed to fetch snapshot data:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteSnapshot = async (id: number) => {
    if (!confirm('Are you sure you want to delete this snapshot?')) return;
    
    try {
      await snapshotApi.deleteSnapshot(id);
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Failed to delete snapshot:', error);
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateForTrends = (dateString: string, period: string) => {
    const date = new Date(dateString);
    switch (period) {
      case 'monthly':
        return date.toLocaleDateString('en-US', { month: 'short' });
      case 'quarterly':
        const quarter = Math.floor(date.getMonth() / 3) + 1;
        return `Q${quarter}'${date.getFullYear().toString().slice(-2)}`;
      case 'yearly':
        return date.getFullYear().toString();
      default:
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const getTrendArrow = (current: number, previous: number) => {
    if (current > previous) return '↗';
    if (current < previous) return '↘';
    return '→';
  };

  const renderTrendRow = (label: string, values: number[], colorClass: string = 'text-white') => (
    <div className="grid grid-cols-5 gap-4 items-center py-2">
      <div className="text-gray-300 font-medium">{label}:</div>
      {values.map((value, index) => (
        <div key={index} className="text-center">
          <div className={`${colorClass} font-medium`}>{formatCurrency(value)}</div>
          {index > 0 && (
            <div className="text-sm text-gray-400 mt-1">
              {getTrendArrow(value, values[index - 1])}
            </div>
          )}
        </div>
      ))}
    </div>
  );

  // Prepare chart data
  const chartData = timelineData ? timelineData.dates.map((date, index) => ({
    date: formatDate(date),
    'Net Worth': timelineData.net_worth[index],
    'Assets': timelineData.assets[index],
    'Liabilities': timelineData.liabilities[index]
  })) : [];

  if (loading) {
    return <div className="flex justify-center p-8"><div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full"></div></div>;
  }

  return (
    <div className="bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <h2 className="text-2xl font-bold text-white">Financial Snapshots</h2>
        
        <div className="flex flex-col sm:flex-row gap-2">
          {/* Period Filter */}
          <div className="flex bg-gray-700 rounded-lg p-1">
            {[
              { key: 'all', label: 'All' },
              { key: 'monthly', label: 'Monthly' },
              { key: 'quarterly', label: 'Quarterly' },
              { key: 'yearly', label: 'Yearly' }
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setPeriod(key as any)}
                className={`px-3 py-1 rounded text-sm ${
                  period === key 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          
          {/* View Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setView('chart')}
              className={`px-4 py-2 rounded-lg ${view === 'chart' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
            >
              Chart
            </button>
            <button
              onClick={() => setView('table')}
              className={`px-4 py-2 rounded-lg ${view === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
            >
              Table
            </button>
          </div>
        </div>
      </div>

      {snapshots.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No snapshots yet. Create your first snapshot to track your financial progress over time.</p>
        </div>
      ) : (
        <>
          {view === 'chart' && chartData.length > 1 && (
            <div className="mb-8">
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis tickFormatter={formatCurrency} />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Legend />
                  <Line type="monotone" dataKey="Net Worth" stroke="#10B981" strokeWidth={2} />
                  <Line type="monotone" dataKey="Assets" stroke="#3B82F6" strokeWidth={2} />
                  <Line type="monotone" dataKey="Liabilities" stroke="#EF4444" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {view === 'table' && detailedSnapshots.length >= 2 && (
            <div className="space-y-6">
              {/* Date Headers */}
              <div className="grid grid-cols-5 gap-4 mb-4">
                <div className="text-gray-400 font-medium"></div>
                {detailedSnapshots.map((snapshot, index) => (
                  <div key={index} className="text-center text-gray-300 text-sm font-medium">
                    {formatDateForTrends(snapshot.snapshot_date, period)}
                  </div>
                ))}
              </div>

              {/* Net Worth Trend */}
              <div className="border-b border-gray-600 pb-4">
                <h3 className="text-lg font-semibold text-white mb-3">Net Worth Trend</h3>
                {renderTrendRow('Net Worth', detailedSnapshots.map(s => s.net_worth), 'text-white font-semibold')}
              </div>

              {/* Asset Breakdown */}
              <div className="border-b border-gray-600 pb-4">
                <h3 className="text-lg font-semibold text-white mb-3">ASSETS</h3>
                {renderTrendRow('Real Estate', detailedSnapshots.map(s => s.categorized.real_estate), 'text-green-400')}
                {renderTrendRow('Investments', detailedSnapshots.map(s => s.categorized.investments), 'text-green-400')}
                {renderTrendRow('Cash', detailedSnapshots.map(s => s.categorized.cash), 'text-green-400')}
                {detailedSnapshots.some(s => s.categorized.other_assets > 0) && 
                  renderTrendRow('Other Assets', detailedSnapshots.map(s => s.categorized.other_assets), 'text-green-400')}
              </div>

              {/* Liability Breakdown */}
              <div className="border-b border-gray-600 pb-4">
                <h3 className="text-lg font-semibold text-white mb-3">LIABILITIES</h3>
                {renderTrendRow('Mortgages', detailedSnapshots.map(s => s.categorized.mortgages), 'text-red-400')}
                {renderTrendRow('Other Debt', detailedSnapshots.map(s => s.categorized.other_debt), 'text-red-400')}
              </div>

              {/* Monthly Cash Flow */}
              <div className="border-b border-gray-600 pb-4">
                <h3 className="text-lg font-semibold text-white mb-3">MONTHLY CASH FLOW</h3>
                {renderTrendRow('Income', detailedSnapshots.map(s => s.monthly_income), 'text-blue-400')}
                {renderTrendRow('Expenses', detailedSnapshots.map(s => s.monthly_expenses), 'text-orange-400')}
                {renderTrendRow('Savings', detailedSnapshots.map(s => s.monthly_income - s.monthly_expenses), 'text-purple-400')}
              </div>

              {/* Manage Snapshots */}
              <div className="pt-4">
                <h3 className="text-lg font-semibold text-white mb-3">Manage Snapshots</h3>
                <div className="space-y-2">
                  {detailedSnapshots.map((snapshot) => (
                    <div key={snapshot.id} className="flex justify-between items-center bg-gray-700 p-3 rounded">
                      <div className="text-gray-300">
                        <span className="font-medium">{formatDate(snapshot.snapshot_date)}</span>
                        <span className="ml-2 text-gray-400">({snapshot.snapshot_name || 'Unnamed'})</span>
                      </div>
                      <button
                        onClick={() => deleteSnapshot(snapshot.id)}
                        className="text-red-400 hover:text-red-300 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {view === 'table' && detailedSnapshots.length < 2 && (
            <div className="text-center py-8 text-gray-400">
              <Calendar className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>At least 2 snapshots are needed to show trends. Create more snapshots to see your financial progress over time.</p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SnapshotTimeline;