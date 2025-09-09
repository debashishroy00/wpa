import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Trash2, Calendar, DollarSign } from 'lucide-react';
import { snapshotApi } from '../services/snapshotApi';
import { Snapshot, TimelineData } from '../types/snapshot';

interface SnapshotTimelineProps {
  refreshTrigger?: number;
}

const SnapshotTimeline: React.FC<SnapshotTimelineProps> = ({ refreshTrigger }) => {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'chart' | 'table'>('chart');

  useEffect(() => {
    fetchData();
  }, [refreshTrigger]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [snapshotsData, chartData] = await Promise.all([
        snapshotApi.getSnapshots(10),
        snapshotApi.getTimelineData()
      ]);
      
      setSnapshots(snapshotsData);
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
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Financial Snapshots</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setView('chart')}
            className={`px-4 py-2 rounded-lg ${view === 'chart' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Chart
          </button>
          <button
            onClick={() => setView('table')}
            className={`px-4 py-2 rounded-lg ${view === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            Table
          </button>
        </div>
      </div>

      {snapshots.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
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

          {view === 'table' && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="px-4 py-3 text-left">Date</th>
                    <th className="px-4 py-3 text-left">Name</th>
                    <th className="px-4 py-3 text-right">Net Worth</th>
                    <th className="px-4 py-3 text-right">Assets</th>
                    <th className="px-4 py-3 text-right">Liabilities</th>
                    <th className="px-4 py-3 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {snapshots.map((snapshot) => (
                    <tr key={snapshot.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3">{formatDate(snapshot.snapshot_date)}</td>
                      <td className="px-4 py-3">{snapshot.snapshot_name || 'Unnamed'}</td>
                      <td className="px-4 py-3 text-right font-medium">
                        {formatCurrency(snapshot.net_worth || 0)}
                      </td>
                      <td className="px-4 py-3 text-right text-green-600">
                        {formatCurrency(snapshot.total_assets || 0)}
                      </td>
                      <td className="px-4 py-3 text-right text-red-600">
                        {formatCurrency(snapshot.total_liabilities || 0)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          onClick={() => deleteSnapshot(snapshot.id)}
                          className="text-red-600 hover:text-red-800 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SnapshotTimeline;