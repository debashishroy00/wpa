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
    <div className="grid grid-cols-5 gap-3 items-center py-0.5">
      <div className="text-gray-300 font-medium text-xs">{label}:</div>
      {values.map((value, index) => (
        <div key={index} className="text-center">
          <div className={`${colorClass} font-medium text-xs`}>{formatCurrency(value)}</div>
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
            <div className="space-y-2">
              {/* Date Headers */}
              <div className="grid grid-cols-5 gap-3 mb-2 pb-1 border-b border-gray-600">
                <div className="text-gray-400 font-medium text-xs"></div>
                {detailedSnapshots.map((snapshot, index) => (
                  <div key={index} className="text-center text-gray-200 text-xs font-semibold">
                    {formatDateForTrends(snapshot.snapshot_date, period)}
                  </div>
                ))}
              </div>

              {/* Net Worth Trend */}
              <div className="bg-gray-750 rounded p-2 border-l-2 border-blue-500">
                <h3 className="text-sm font-bold text-white mb-1 uppercase tracking-wide">Net Worth</h3>
                {renderTrendRow('Net Worth', detailedSnapshots.map(s => s.net_worth), 'text-white font-bold')}
              </div>

              {/* Asset Breakdown */}
              <div className="bg-gray-750 rounded p-2 border-l-2 border-green-500">
                <h3 className="text-sm font-bold text-green-400 mb-1 uppercase tracking-wide">Assets</h3>
                <div className="space-y-0">
                  {renderTrendRow('Real Estate', detailedSnapshots.map(s => s.categorized.real_estate), 'text-green-400')}
                  {renderTrendRow('Investments', detailedSnapshots.map(s => s.categorized.investments), 'text-green-400')}
                  {renderTrendRow('Cash', detailedSnapshots.map(s => s.categorized.cash), 'text-green-400')}
                  {detailedSnapshots.some(s => s.categorized.other_assets > 0) && 
                    renderTrendRow('Other Assets', detailedSnapshots.map(s => s.categorized.other_assets), 'text-green-400')}
                </div>
              </div>

              {/* Liability Breakdown */}
              <div className="bg-gray-750 rounded p-2 border-l-2 border-red-500">
                <h3 className="text-sm font-bold text-red-400 mb-1 uppercase tracking-wide">Liabilities</h3>
                <div className="space-y-0">
                  {renderTrendRow('Mortgages', detailedSnapshots.map(s => s.categorized.mortgages), 'text-red-400')}
                  {renderTrendRow('Other Debt', detailedSnapshots.map(s => s.categorized.other_debt), 'text-red-400')}
                </div>
              </div>

              {/* Monthly Cash Flow */}
              <div className="bg-gray-750 rounded p-2 border-l-2 border-purple-500">
                <h3 className="text-sm font-bold text-purple-400 mb-1 uppercase tracking-wide">Monthly Cash Flow</h3>
                <div className="space-y-0">
                  {renderTrendRow('Income', detailedSnapshots.map(s => s.monthly_income), 'text-blue-400')}
                  {renderTrendRow('Expenses', detailedSnapshots.map(s => s.monthly_expenses), 'text-orange-400')}
                  {renderTrendRow('Savings', detailedSnapshots.map(s => s.monthly_income - s.monthly_expenses), 'text-purple-400')}
                  <div className="grid grid-cols-5 gap-3 items-center py-0.5">
                    <div className="text-gray-300 font-medium text-xs">Savings Rate:</div>
                    {detailedSnapshots.map((snapshot, index) => {
                      const savingsRate = snapshot.monthly_income > 0 
                        ? ((snapshot.monthly_income - snapshot.monthly_expenses) / snapshot.monthly_income * 100)
                        : 0;
                      return (
                        <div key={index} className="text-center">
                          <div className="text-green-400 font-medium text-xs">{savingsRate.toFixed(1)}%</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Manage Snapshots */}
              <div className="bg-gray-750 rounded p-2 border-l-2 border-gray-500">
                <h3 className="text-sm font-bold text-gray-300 mb-1 uppercase tracking-wide">Manage Snapshots</h3>
                <div className="space-y-0">
                  {detailedSnapshots.map((snapshot) => (
                    <div key={snapshot.id} className="flex justify-between items-center bg-gray-700 p-1 rounded text-xs">
                      <div className="text-gray-300">
                        <span className="font-medium">{formatDate(snapshot.snapshot_date)}</span>
                        <span className="ml-1 text-gray-400">({snapshot.snapshot_name || 'Unnamed'})</span>
                      </div>
                      <button
                        onClick={() => deleteSnapshot(snapshot.id)}
                        className="text-red-400 hover:text-red-300 transition-colors"
                      >
                        <Trash2 className="w-3 h-3" />
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