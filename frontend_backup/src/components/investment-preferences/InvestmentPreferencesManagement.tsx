import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import Input from '../ui/Input';
import { 
  Plus, 
  Edit3, 
  Trash2, 
  TrendingUp, 
  PieChart, 
  Target,
  BarChart3,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

interface InvestmentPreferences {
  id: number;
  risk_tolerance_score?: number;
  investment_timeline_years?: number;
  rebalancing_frequency?: string;
  investment_philosophy?: string;
  esg_preference_level?: number;
  international_allocation_target?: number;
  alternative_investment_interest?: number;
  cryptocurrency_allocation?: number;
  individual_stock_tolerance?: number;
  tax_loss_harvesting_enabled?: boolean;
  dollar_cost_averaging_preference?: boolean;
  sector_preferences?: any;
  created_at?: string;
  updated_at?: string;
}

const InvestmentPreferencesManagement: React.FC = () => {
  const [preferences, setPreferences] = useState<InvestmentPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<Partial<InvestmentPreferences>>({
    risk_tolerance_score: 5,
    investment_timeline_years: 10,
    rebalancing_frequency: 'quarterly',
    investment_philosophy: 'passive',
    esg_preference_level: 3,
    international_allocation_target: 20,
    alternative_investment_interest: 0,
    cryptocurrency_allocation: 0,
    individual_stock_tolerance: 0,
    tax_loss_harvesting_enabled: false,
    dollar_cost_averaging_preference: true
  });

  // Use smart API URL detection
  const getApiBaseUrl = () => {
    const hostname = window.location.hostname;
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return 'https://wealthpath-backend.onrender.com';
    }
    return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  };
  const API_BASE = getApiBaseUrl();

  const getAuthToken = () => {
    return localStorage.getItem('access_token');
  };

  const apiCall = async (url: string, options: RequestInit = {}) => {
    const token = getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  };

  const loadPreferences = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await apiCall('/api/v1/investment-preferences/');
      setPreferences(data);
      setFormData(data);
      
    } catch (err: any) {
      if (err.message.includes('404')) {
        setPreferences(null);
      } else {
        setError(err.message);
      }
      console.error('Error loading investment preferences:', err);
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    try {
      setError(null);
      
      const method = preferences ? 'PUT' : 'POST';
      const data = await apiCall('/api/v1/investment-preferences/', {
        method,
        body: JSON.stringify(formData)
      });
      
      setPreferences(data);
      setShowForm(false);
      
    } catch (err: any) {
      setError(err.message);
      console.error('Error saving investment preferences:', err);
    }
  };

  const deletePreferences = async () => {
    if (!confirm('Are you sure you want to delete your investment preferences? This action cannot be undone.')) {
      return;
    }

    try {
      setError(null);
      
      await apiCall('/api/v1/investment-preferences/', {
        method: 'DELETE'
      });
      
      setPreferences(null);
      setFormData({
        risk_tolerance_score: 5,
        investment_timeline_years: 10,
        rebalancing_frequency: 'quarterly',
        investment_philosophy: 'passive',
        esg_preference_level: 3,
        international_allocation_target: 20,
        alternative_investment_interest: false,
        cryptocurrency_allocation: 0,
        individual_stock_tolerance: false,
        tax_loss_harvesting_enabled: false,
        dollar_cost_averaging_preference: true
      });
      
    } catch (err: any) {
      setError(err.message);
      console.error('Error deleting investment preferences:', err);
    }
  };

  const getRiskProfile = (score?: number) => {
    if (!score) return 'Unknown';
    if (score <= 3) return 'Conservative';
    if (score <= 6) return 'Moderate';
    if (score <= 8) return 'Moderate-Aggressive';
    return 'Aggressive';
  };

  const getTimelineCategory = (years?: number) => {
    if (!years) return 'Unknown';
    if (years <= 5) return 'Short-term';
    if (years <= 15) return 'Medium-term';
    return 'Long-term';
  };

  useEffect(() => {
    loadPreferences();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <Card className="bg-red-900/20 border-red-500/20 p-4">
          <div className="flex items-center space-x-2 text-red-400">
            <AlertCircle className="h-4 w-4" />
            <span>Error: {error}</span>
          </div>
        </Card>
      )}

      {/* Preferences Summary */}
      <Card className="bg-gray-800 border-gray-700">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-blue-400" />
              <h3 className="text-white text-lg font-semibold">Investment Preferences</h3>
            </div>
            <div className="flex gap-3">
              {preferences && (
                <Button
                  variant="outline"
                  onClick={deletePreferences}
                  className="text-red-400 hover:text-red-300 border-red-500/20"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </Button>
              )}
              <Button
                onClick={() => setShowForm(!showForm)}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {preferences ? <Edit3 className="w-4 h-4 mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
                {preferences ? 'Edit Preferences' : 'Set Preferences'}
              </Button>
            </div>
          </div>

          {preferences ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-gray-700 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Target className="h-4 w-4 text-green-400" />
                  <span className="text-white font-medium">Risk Profile</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {getRiskProfile(preferences.risk_tolerance_score)}
                </p>
                <p className="text-gray-400 text-sm">
                  Score: {preferences.risk_tolerance_score}/10
                </p>
              </div>

              <div className="bg-gray-700 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <Clock className="h-4 w-4 text-blue-400" />
                  <span className="text-white font-medium">Timeline</span>
                </div>
                <p className="text-2xl font-bold text-white">
                  {getTimelineCategory(preferences.investment_timeline_years)}
                </p>
                <p className="text-gray-400 text-sm">
                  {preferences.investment_timeline_years} years
                </p>
              </div>

              <div className="bg-gray-700 p-4 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <PieChart className="h-4 w-4 text-purple-400" />
                  <span className="text-white font-medium">Philosophy</span>
                </div>
                <p className="text-2xl font-bold text-white capitalize">
                  {preferences.investment_philosophy || 'Not Set'}
                </p>
                <p className="text-gray-400 text-sm">
                  {preferences.rebalancing_frequency} rebalancing
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <BarChart3 className="w-16 h-16 text-gray-500 mx-auto mb-4" />
              <p className="text-gray-400 mb-4">No investment preferences set</p>
              <p className="text-gray-500 text-sm">
                Set your investment preferences to receive personalized recommendations
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Preferences Form */}
      {showForm && (
        <Card className="bg-gray-800 border-gray-700">
          <div className="p-6">
            <h3 className="text-white text-lg font-semibold mb-4">Investment Preferences</h3>
            
            <div className="space-y-6">
              {/* Risk Tolerance */}
              <div>
                <label className="text-white block mb-2">Risk Tolerance (1-10)</label>
                <div className="flex items-center space-x-4">
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={formData.risk_tolerance_score || 5}
                    onChange={(e) => setFormData({...formData, risk_tolerance_score: parseInt(e.target.value)})}
                    className="flex-1"
                  />
                  <span className="text-white w-8">{formData.risk_tolerance_score}</span>
                </div>
                <p className="text-gray-400 text-sm mt-1">
                  Current: {getRiskProfile(formData.risk_tolerance_score)}
                </p>
              </div>

              {/* Investment Timeline */}
              <div>
                <label className="text-white block mb-2">Investment Timeline (years)</label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  value={formData.investment_timeline_years || ''}
                  onChange={(e) => setFormData({...formData, investment_timeline_years: parseInt(e.target.value)})}
                  className="bg-gray-700 border-gray-600 text-white"
                  placeholder="e.g. 15"
                />
              </div>

              {/* Investment Philosophy */}
              <div>
                <label className="text-white block mb-2">Investment Philosophy</label>
                <select
                  value={formData.investment_philosophy || 'passive'}
                  onChange={(e) => setFormData({...formData, investment_philosophy: e.target.value})}
                  className="w-full p-2 bg-gray-700 border border-gray-600 text-white rounded"
                >
                  <option value="passive">Passive</option>
                  <option value="active">Active</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="value">Value</option>
                  <option value="growth">Growth</option>
                </select>
              </div>

              {/* Rebalancing Frequency */}
              <div>
                <label className="text-white block mb-2">Rebalancing Frequency</label>
                <select
                  value={formData.rebalancing_frequency || 'quarterly'}
                  onChange={(e) => setFormData({...formData, rebalancing_frequency: e.target.value})}
                  className="w-full p-2 bg-gray-700 border border-gray-600 text-white rounded"
                >
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="annual">Annual</option>
                  <option value="threshold">Threshold-based</option>
                </select>
              </div>

              {/* International Allocation */}
              <div>
                <label className="text-white block mb-2">International Allocation Target (%)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.international_allocation_target || ''}
                  onChange={(e) => setFormData({...formData, international_allocation_target: parseFloat(e.target.value)})}
                  className="bg-gray-700 border-gray-600 text-white"
                  placeholder="e.g. 20"
                />
              </div>

              {/* Checkboxes */}
              <div className="space-y-3">
                <label className="flex items-center space-x-2 text-white">
                  <input
                    type="checkbox"
                    checked={formData.alternative_investment_interest || false}
                    onChange={(e) => setFormData({...formData, alternative_investment_interest: e.target.checked})}
                    className="rounded"
                  />
                  <span>Interest in alternative investments</span>
                </label>

                <label className="flex items-center space-x-2 text-white">
                  <input
                    type="checkbox"
                    checked={formData.individual_stock_tolerance || false}
                    onChange={(e) => setFormData({...formData, individual_stock_tolerance: e.target.checked})}
                    className="rounded"
                  />
                  <span>Comfortable with individual stocks</span>
                </label>

                <label className="flex items-center space-x-2 text-white">
                  <input
                    type="checkbox"
                    checked={formData.tax_loss_harvesting_enabled || false}
                    onChange={(e) => setFormData({...formData, tax_loss_harvesting_enabled: e.target.checked})}
                    className="rounded"
                  />
                  <span>Enable tax-loss harvesting</span>
                </label>

                <label className="flex items-center space-x-2 text-white">
                  <input
                    type="checkbox"
                    checked={formData.dollar_cost_averaging_preference || false}
                    onChange={(e) => setFormData({...formData, dollar_cost_averaging_preference: e.target.checked})}
                    className="rounded"
                  />
                  <span>Prefer dollar-cost averaging</span>
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t border-gray-600">
                <Button
                  onClick={savePreferences}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Save Preferences
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowForm(false)}
                  className="border-gray-600 text-gray-300 hover:text-white"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default InvestmentPreferencesManagement;