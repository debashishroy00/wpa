/**
 * Insurance Management Component
 * Comprehensive insurance policy management with different policy types
 */
import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Plus, 
  Edit, 
  Trash2, 
  DollarSign, 
  Users, 
  Car, 
  Home,
  Heart,
  Briefcase,
  Umbrella,
  Plane,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { apiClient } from '../../utils/api-simple';

interface InsurancePolicy {
  id: string;
  policy_type: string;
  policy_name: string;
  coverage_amount?: number;
  annual_premium?: number;
  beneficiary_primary?: string;
  beneficiary_secondary?: string;
  policy_details?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface PolicyFormData {
  policy_type: string;
  policy_name: string;
  coverage_amount: string;
  annual_premium: string;
  beneficiary_primary: string;
  beneficiary_secondary: string;
}

interface InsuranceSummary {
  total_policies: number;
  total_annual_premiums: number;
  coverage_by_type: Record<string, {
    count: number;
    total_coverage: number;
    total_premiums: number;
    policies: Array<{
      id: string;
      name: string;
      coverage: number;
      premium: number;
    }>;
  }>;
}

const POLICY_TYPE_CONFIG = {
  life: { 
    icon: Heart, 
    label: 'Life Insurance', 
    color: 'text-red-500',
    description: 'Life insurance protection for beneficiaries'
  },
  disability: { 
    icon: Briefcase, 
    label: 'Disability Insurance', 
    color: 'text-orange-500',
    description: 'Income protection if unable to work'
  },
  health: { 
    icon: Shield, 
    label: 'Health Insurance', 
    color: 'text-green-500',
    description: 'Medical coverage and healthcare expenses'
  },
  auto: { 
    icon: Car, 
    label: 'Auto Insurance', 
    color: 'text-blue-500',
    description: 'Vehicle coverage and liability protection'
  },
  homeowners: { 
    icon: Home, 
    label: 'Homeowners Insurance', 
    color: 'text-purple-500',
    description: 'Property and liability protection for homes'
  },
  umbrella: { 
    icon: Umbrella, 
    label: 'Umbrella Insurance', 
    color: 'text-indigo-500',
    description: 'Additional liability coverage'
  },
  renters: { 
    icon: Home, 
    label: 'Renters Insurance', 
    color: 'text-teal-500',
    description: 'Personal property protection for renters'
  },
  travel: { 
    icon: Plane, 
    label: 'Travel Insurance', 
    color: 'text-pink-500',
    description: 'Coverage for travel-related incidents'
  }
};

const InsuranceManagement: React.FC = () => {
  const [policies, setPolicies] = useState<InsurancePolicy[]>([]);
  const [summary, setSummary] = useState<InsuranceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<InsurancePolicy | null>(null);
  const [formData, setFormData] = useState<PolicyFormData>({
    policy_type: 'life',
    policy_name: '',
    coverage_amount: '',
    annual_premium: '',
    beneficiary_primary: '',
    beneficiary_secondary: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [policyTypes, setPolicyTypes] = useState<Array<{value: string; label: string; description: string}>>([]);

  useEffect(() => {
    loadInsuranceData();
    fetchPolicyTypes();
  }, []);

  const fetchPolicyTypes = async () => {
    try {
      const response = await apiClient.get('/api/v1/insurance/policy-types');
      setPolicyTypes(response.policy_types || []);
    } catch (error) {
      console.error('Failed to fetch policy types:', error);
    }
  };

  const loadInsuranceData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [policiesData, summaryData] = await Promise.all([
        apiClient.get('/api/v1/insurance/policies'),
        apiClient.get('/api/v1/insurance/policies/summary')
      ]);
      
      setPolicies(policiesData);
      setSummary(summaryData);
      
    } catch (err) {
      console.error('Failed to load insurance data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load insurance data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePolicy = async (policyId: string) => {
    if (!confirm('Are you sure you want to delete this insurance policy?')) {
      return;
    }

    try {
      await apiClient.delete(`/api/v1/insurance/policies/${policyId}`);
      await loadInsuranceData(); // Refresh data
    } catch (err) {
      console.error('Failed to delete policy:', err);
      setError('Failed to delete policy');
    }
  };

  const resetForm = () => {
    setFormData({
      policy_type: 'life',
      policy_name: '',
      coverage_amount: '',
      annual_premium: '',
      beneficiary_primary: '',
      beneficiary_secondary: ''
    });
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.policy_name.trim()) {
      setError('Policy name is required');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        policy_type: formData.policy_type,
        policy_name: formData.policy_name.trim(),
        coverage_amount: formData.coverage_amount ? parseFloat(formData.coverage_amount) : undefined,
        annual_premium: formData.annual_premium ? parseFloat(formData.annual_premium) : undefined,
        beneficiary_primary: formData.beneficiary_primary.trim() || undefined,
        beneficiary_secondary: formData.beneficiary_secondary.trim() || undefined,
        policy_details: {}
      };

      if (editingPolicy) {
        await apiClient.put(`/api/v1/insurance/policies/${editingPolicy.id}`, payload);
        setEditingPolicy(null);
      } else {
        await apiClient.post('/api/v1/insurance/policies', payload);
        setShowAddModal(false);
      }

      resetForm();
      await loadInsuranceData();
    } catch (error: any) {
      console.error('Failed to save policy:', error);
      setError(error.response?.data?.detail || 'Failed to save policy');
    } finally {
      setSubmitting(false);
    }
  };

  const openEditModal = (policy: InsurancePolicy) => {
    setFormData({
      policy_type: policy.policy_type,
      policy_name: policy.policy_name,
      coverage_amount: policy.coverage_amount?.toString() || '',
      annual_premium: policy.annual_premium?.toString() || '',
      beneficiary_primary: policy.beneficiary_primary || '',
      beneficiary_secondary: policy.beneficiary_secondary || ''
    });
    setEditingPolicy(policy);
    setError(null);
  };

  const openAddModal = () => {
    resetForm();
    setShowAddModal(true);
    setError(null);
  };

  const formatCurrency = (amount: number | null | undefined) => {
    if (!amount) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getPolicyTypeIcon = (policyType: string) => {
    const config = POLICY_TYPE_CONFIG[policyType as keyof typeof POLICY_TYPE_CONFIG];
    if (!config) return Shield;
    return config.icon;
  };

  const getPolicyTypeColor = (policyType: string) => {
    const config = POLICY_TYPE_CONFIG[policyType as keyof typeof POLICY_TYPE_CONFIG];
    return config?.color || 'text-gray-500';
  };

  if (loading) {
    return (
      <Card className="w-full">
        <Card.Body>
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading insurance policies...</span>
          </div>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full border-red-200">
        <Card.Body>
          <div className="flex items-center text-red-600">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>{error}</span>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={loadInsuranceData}
              className="ml-4"
            >
              Retry
            </Button>
          </div>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <Card.Body>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">Total Policies</p>
                <p className="text-2xl font-bold text-white">
                  {summary?.total_policies || 0}
                </p>
              </div>
              <Shield className="w-8 h-8 text-blue-500" />
            </div>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">Annual Premiums</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(summary?.total_annual_premiums || 0)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">Coverage Types</p>
                <p className="text-2xl font-bold text-white">
                  {summary ? Object.keys(summary.coverage_by_type).length : 0}
                </p>
              </div>
              <Umbrella className="w-8 h-8 text-purple-500" />
            </div>
          </Card.Body>
        </Card>
      </div>

      {/* Main Insurance Policies */}
      <Card>
        <Card.Header>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Insurance Policies</h3>
            <Button onClick={openAddModal}>
              <Plus className="w-4 h-4 mr-2" />
              Add Policy
            </Button>
          </div>
        </Card.Header>
        
        <Card.Body>
          {policies.length === 0 ? (
            <div className="text-center py-12">
              <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Insurance Policies</h3>
              <p className="text-gray-500 mb-4">
                Start protecting your financial future by adding your insurance policies
              </p>
              <Button onClick={() => setShowAddModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Policy
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Group policies by type */}
              {Object.entries(summary?.coverage_by_type || {}).map(([policyType, typeData]) => {
                const Icon = getPolicyTypeIcon(policyType);
                const config = POLICY_TYPE_CONFIG[policyType as keyof typeof POLICY_TYPE_CONFIG];
                const typePolicies = policies.filter(p => p.policy_type === policyType);
                
                return (
                  <div key={policyType} className="border border-gray-700 rounded-lg p-4 bg-gray-800">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <Icon className={`w-6 h-6 ${getPolicyTypeColor(policyType)}`} />
                        <div>
                          <h4 className="font-medium text-white">{config?.label}</h4>
                          <p className="text-sm text-white">
                            {typeData.count} policies • {formatCurrency(typeData.total_coverage)} coverage
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-white">
                          {formatCurrency(typeData.total_premiums)}
                        </p>
                        <p className="text-sm text-white">annual premium</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {typePolicies.map((policy) => (
                        <div key={policy.id} className="bg-gray-800 border border-gray-700 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="font-medium text-white">{policy.policy_name}</h5>
                            <div className="flex items-center space-x-1">
                              <button
                                onClick={() => openEditModal(policy)}
                                className="p-1 text-gray-300 hover:text-white transition-colors"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeletePolicy(policy.id)}
                                className="p-1 text-gray-300 hover:text-white transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                          
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <p className="text-white">Coverage</p>
                              <p className="font-medium text-white">{formatCurrency(policy.coverage_amount)}</p>
                            </div>
                            <div>
                              <p className="text-white">Premium</p>
                              <p className="font-medium text-white">{formatCurrency(policy.annual_premium)}</p>
                            </div>
                            {policy.beneficiary_primary && (
                              <div className="col-span-2">
                                <p className="text-white">Primary Beneficiary</p>
                                <p className="font-medium text-white">{policy.beneficiary_primary}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Add Policy Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Add Insurance Policy</h3>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Policy Type *
                </label>
                <select
                  value={formData.policy_type}
                  onChange={(e) => setFormData({...formData, policy_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {policyTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Policy Name *
                </label>
                <input
                  type="text"
                  value={formData.policy_name}
                  onChange={(e) => setFormData({...formData, policy_name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Term Life Insurance Policy"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Coverage Amount
                </label>
                <input
                  type="number"
                  value={formData.coverage_amount}
                  onChange={(e) => setFormData({...formData, coverage_amount: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="500000"
                  min="0"
                  step="1000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Annual Premium
                </label>
                <input
                  type="number"
                  value={formData.annual_premium}
                  onChange={(e) => setFormData({...formData, annual_premium: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="1200"
                  min="0"
                  step="10"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Primary Beneficiary
                </label>
                <input
                  type="text"
                  value={formData.beneficiary_primary}
                  onChange={(e) => setFormData({...formData, beneficiary_primary: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Spouse name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Secondary Beneficiary
                </label>
                <input
                  type="text"
                  value={formData.beneficiary_secondary}
                  onChange={(e) => setFormData({...formData, beneficiary_secondary: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Children or other beneficiary"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button 
                  type="button"
                  variant="outline" 
                  onClick={() => setShowAddModal(false)}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit"
                  disabled={submitting}
                >
                  {submitting ? 'Saving...' : 'Save Policy'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Policy Modal */}
      {editingPolicy && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Edit Insurance Policy</h3>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Policy Type *
                </label>
                <select
                  value={formData.policy_type}
                  onChange={(e) => setFormData({...formData, policy_type: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  {policyTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Policy Name *
                </label>
                <input
                  type="text"
                  value={formData.policy_name}
                  onChange={(e) => setFormData({...formData, policy_name: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Term Life Insurance Policy"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Coverage Amount
                </label>
                <input
                  type="number"
                  value={formData.coverage_amount}
                  onChange={(e) => setFormData({...formData, coverage_amount: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="500000"
                  min="0"
                  step="1000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Annual Premium
                </label>
                <input
                  type="number"
                  value={formData.annual_premium}
                  onChange={(e) => setFormData({...formData, annual_premium: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="1200"
                  min="0"
                  step="10"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Primary Beneficiary
                </label>
                <input
                  type="text"
                  value={formData.beneficiary_primary}
                  onChange={(e) => setFormData({...formData, beneficiary_primary: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Spouse name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Secondary Beneficiary
                </label>
                <input
                  type="text"
                  value={formData.beneficiary_secondary}
                  onChange={(e) => setFormData({...formData, beneficiary_secondary: e.target.value})}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Children or other beneficiary"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button 
                  type="button"
                  variant="outline" 
                  onClick={() => setEditingPolicy(null)}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit"
                  disabled={submitting}
                >
                  {submitting ? 'Updating...' : 'Update Policy'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InsuranceManagement;