import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import { 
  Heart, 
  DollarSign, 
  Calendar, 
  TrendingUp, 
  Shield,
  Calculator,
  PieChart,
  AlertCircle,
  CheckCircle,
  Plus,
  Edit,
  Trash2,
  Save,
  Loader2
} from 'lucide-react';

interface BenefitData {
  id: number;
  benefit_type: string;
  benefit_name: string;
  estimated_monthly_benefit?: number;
  full_retirement_age?: number;
  employer_match_percentage?: number;
  employer_match_limit?: number;
  // Enhanced fields
  social_security_estimated_benefit?: number;
  social_security_claiming_age?: number;
  employer_401k_match_formula?: string;
  employer_401k_vesting_schedule?: string;
  pension_details?: any;
  other_benefits?: any;
}

interface BenefitsData {
  benefits: BenefitData[];
}

const EnhancedBenefitsManagement: React.FC = () => {
  const [benefitsData, setBenefitsData] = useState<BenefitsData>({ benefits: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSocialSecurityForm, setShowSocialSecurityForm] = useState(false);
  const [show401kForm, setShow401kForm] = useState(false);
  const [showPensionForm, setShowPensionForm] = useState(false);
  const [socialSecurityData, setSocialSecurityData] = useState({
    estimated_benefit: '',
    claiming_age: '67',
    full_retirement_age: '67'
  });
  const [k401Data, set401kData] = useState({
    match_formula: '',
    vesting_schedule: '',
    employer_contribution: '',
    max_contribution: ''
  });
  const [pensionData, setPensionData] = useState({
    pension_type: 'defined_benefit',
    monthly_payout: '',
    vesting_schedule: '',
    lump_sum_available: false
  });

  // Save state management
  const [isSavingSocialSecurity, setIsSavingSocialSecurity] = useState(false);
  const [isSaving401k, setIsSaving401k] = useState(false);
  const [socialSecuritySaveSuccess, setSocialSecuritySaveSuccess] = useState(false);
  const [k401SaveSuccess, set401kSaveSuccess] = useState(false);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

  const loadBenefitsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiCall('/api/v1/profile/complete-profile');
      setBenefitsData({ benefits: response.benefits || [] });
      
      // Load saved Social Security data
      const socialSecurityBenefit = response.benefits?.find((b: any) => b.benefit_type === 'social_security');
      if (socialSecurityBenefit) {
        setSocialSecurityData(prev => ({
          ...prev,
          estimated_benefit: socialSecurityBenefit.estimated_monthly_benefit?.toString() || '',
          claiming_age: socialSecurityBenefit.social_security_claiming_age?.toString() || '67',
          full_retirement_age: socialSecurityBenefit.full_retirement_age?.toString() || '67'
        }));
      }
      
      // Load saved 401(k) data
      const k401Benefit = response.benefits?.find((b: any) => b.benefit_type === '401k');
      if (k401Benefit) {
        set401kData(prev => ({
          ...prev,
          match_formula: k401Benefit.employer_401k_match_formula || '',
          vesting_schedule: k401Benefit.employer_401k_vesting_schedule || '',
          employer_contribution: k401Benefit.employer_contribution?.toString() || '',
          max_contribution: k401Benefit.max_401k_contribution?.toString() || ''
        }));
      }
      
    } catch (err: any) {
      setError(err.message);
      console.error('Error loading benefits data:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateSocialSecurityOptimization = () => {
    const claimingAge = parseInt(socialSecurityData.claiming_age);
    const fullRetirementAge = parseInt(socialSecurityData.full_retirement_age);
    const estimatedBenefit = parseFloat(socialSecurityData.estimated_benefit);

    if (!estimatedBenefit || !claimingAge) return null;

    let adjustmentFactor = 1;
    
    if (claimingAge < fullRetirementAge) {
      // Early retirement reduction: approximately 6.67% per year before FRA
      const yearsEarly = fullRetirementAge - claimingAge;
      adjustmentFactor = 1 - (yearsEarly * 0.0667);
    } else if (claimingAge > fullRetirementAge) {
      // Delayed retirement credits: 8% per year after FRA until age 70
      const yearsDelayed = Math.min(claimingAge - fullRetirementAge, 70 - fullRetirementAge);
      adjustmentFactor = 1 + (yearsDelayed * 0.08);
    }

    const adjustedBenefit = estimatedBenefit * adjustmentFactor;
    const annualBenefit = adjustedBenefit * 12;

    return {
      monthlyBenefit: adjustedBenefit,
      annualBenefit: annualBenefit,
      adjustmentFactor: adjustmentFactor,
      recommendation: claimingAge < fullRetirementAge ? 
        'Consider waiting until Full Retirement Age for full benefits' :
        claimingAge > 70 ? 
        'No additional credits after age 70' :
        'Optimal claiming strategy depends on your health and financial needs'
    };
  };

  const calculate401kProjection = () => {
    const matchFormula = k401Data.match_formula;
    const employerContribution = parseFloat(k401Data.employer_contribution) || 0;
    
    if (!matchFormula) return null;

    // Parse common match formulas
    let maxMatch = 0;
    let recommendations = [];

    if (matchFormula.includes('100%') && matchFormula.includes('3%')) {
      maxMatch = employerContribution * 0.03;
      recommendations.push('Contribute at least 3% to get full employer match');
    } else if (matchFormula.includes('50%') && matchFormula.includes('6%')) {
      maxMatch = employerContribution * 0.06 * 0.5;
      recommendations.push('Contribute at least 6% to maximize employer match');
    }

    return {
      maxMatch: maxMatch,
      recommendations: recommendations,
      annualMatch: maxMatch * 12
    };
  };

  // Save handlers
  const handleSaveSocialSecurity = async () => {
    setIsSavingSocialSecurity(true);
    setSocialSecuritySaveSuccess(false);
    
    try {
      const response = await apiCall('/api/v1/profile/social-security', {
        method: 'POST',
        body: JSON.stringify({
          estimated_monthly_benefit: parseFloat(socialSecurityData.estimated_benefit) || 0,
          planned_claiming_age: parseInt(socialSecurityData.claiming_age) || 67,
          full_retirement_age: parseInt(socialSecurityData.full_retirement_age) || 67
        })
      });

      if (response.status === 'success') {
        setSocialSecuritySaveSuccess(true);
        setTimeout(() => setSocialSecuritySaveSuccess(false), 3000);
      }
    } catch (error) {
      console.error('Failed to save Social Security data:', error);
      setError('Failed to save Social Security data. Please try again.');
    } finally {
      setIsSavingSocialSecurity(false);
    }
  };

  const handleSave401k = async () => {
    setIsSaving401k(true);
    set401kSaveSuccess(false);
    
    try {
      const response = await apiCall('/api/v1/profile/401k', {
        method: 'POST',
        body: JSON.stringify({
          employer_match_formula: k401Data.match_formula || '',
          vesting_schedule: k401Data.vesting_schedule || '',
          annual_salary: parseFloat(k401Data.employer_contribution) || 0,
          annual_401k_limit: parseFloat(k401Data.max_contribution) || 23000
        })
      });

      if (response.status === 'success') {
        set401kSaveSuccess(true);
        // Trigger vector store sync for complete context update
        await apiCall('/api/v1/profile/sync-vector-store', {
          method: 'POST'
        });
        setTimeout(() => set401kSaveSuccess(false), 3000);
      }
    } catch (error) {
      console.error('Failed to save 401(k) data:', error);
      setError('Failed to save 401(k) data. Please try again.');
    } finally {
      setIsSaving401k(false);
    }
  };

  useEffect(() => {
    loadBenefitsData();
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

      {/* Benefits Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gray-800 border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Social Security</p>
              <p className="text-white text-2xl font-bold">
                ${socialSecurityData.estimated_benefit ? 
                  parseFloat(socialSecurityData.estimated_benefit).toLocaleString() : 
                  'Not Set'}
              </p>
              <p className="text-white text-sm">Monthly at claiming age {socialSecurityData.claiming_age}</p>
            </div>
            <DollarSign className="h-8 w-8 text-green-400" />
          </div>
        </Card>

        <Card className="bg-gray-800 border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">401(k) Match</p>
              <p className="text-white text-2xl font-bold">
                {k401Data.match_formula || 'Not Set'}
              </p>
              <p className="text-white text-sm">Employer matching formula</p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-400" />
          </div>
        </Card>

        <Card className="bg-gray-800 border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white font-medium">Benefits Count</p>
              <p className="text-white text-2xl font-bold">
                {benefitsData.benefits.length}
              </p>
              <p className="text-white text-sm">Total benefits tracked</p>
            </div>
            <Heart className="h-8 w-8 text-purple-400" />
          </div>
        </Card>
      </div>

      {/* Social Security Optimization */}
      <Card className="bg-gray-800 border-gray-700">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-green-400" />
              <h3 className="text-white text-lg font-semibold">Social Security Optimization</h3>
            </div>
            <Button 
              onClick={() => setShowSocialSecurityForm(!showSocialSecurityForm)}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {showSocialSecurityForm ? 'Hide' : 'Configure'}
            </Button>
          </div>

          {showSocialSecurityForm && (
            <div className="bg-gray-900 p-4 rounded-lg space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-white block mb-2">Estimated Monthly Benefit at FRA</label>
                  <Input
                    type="number"
                    placeholder="e.g. 3200"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={socialSecurityData.estimated_benefit}
                    onChange={(e) => setSocialSecurityData({...socialSecurityData, estimated_benefit: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-white block mb-2">Planned Claiming Age</label>
                  <select 
                    className="w-full p-2 bg-gray-800 border border-gray-600 text-white rounded"
                    value={socialSecurityData.claiming_age}
                    onChange={(e) => setSocialSecurityData({...socialSecurityData, claiming_age: e.target.value})}
                  >
                    <option value="62">62 (Early, Reduced)</option>
                    <option value="65">65</option>
                    <option value="67">67 (Full Retirement Age)</option>
                    <option value="68">68</option>
                    <option value="69">69</option>
                    <option value="70">70 (Maximum Credits)</option>
                  </select>
                </div>
                <div>
                  <label className="text-white block mb-2">Full Retirement Age</label>
                  <select 
                    className="w-full p-2 bg-gray-800 border border-gray-600 text-white rounded"
                    value={socialSecurityData.full_retirement_age}
                    onChange={(e) => setSocialSecurityData({...socialSecurityData, full_retirement_age: e.target.value})}
                  >
                    <option value="66">66</option>
                    <option value="67">67</option>
                  </select>
                </div>
              </div>

              {socialSecurityData.estimated_benefit && (
                <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                  {(() => {
                    const optimization = calculateSocialSecurityOptimization();
                    return optimization ? (
                      <div>
                        <h4 className="text-white font-medium mb-2">Benefit Calculation</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-gray-400">Adjusted Monthly Benefit</p>
                            <p className="text-white font-bold">${optimization.monthlyBenefit.toLocaleString()}</p>
                          </div>
                          <div>
                            <p className="text-gray-400">Annual Benefit</p>
                            <p className="text-white font-bold">${optimization.annualBenefit.toLocaleString()}</p>
                          </div>
                          <div>
                            <p className="text-gray-400">Adjustment Factor</p>
                            <p className="text-white font-bold">{(optimization.adjustmentFactor * 100).toFixed(1)}%</p>
                          </div>
                        </div>
                        <div className="mt-3 p-3 bg-blue-900/30 rounded border border-blue-500/20">
                          <p className="text-blue-300 text-sm">{optimization.recommendation}</p>
                        </div>
                      </div>
                    ) : null;
                  })()}
                </div>
              )}

              {/* Save Button for Social Security */}
              <div className="flex justify-end mt-4 pt-4 border-t border-gray-700">
                <Button
                  onClick={handleSaveSocialSecurity}
                  disabled={isSavingSocialSecurity}
                  className={`
                    px-4 py-2 font-medium transition-all flex items-center space-x-2
                    ${isSavingSocialSecurity 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : socialSecuritySaveSuccess 
                        ? 'bg-green-500 hover:bg-green-600' 
                        : 'bg-blue-500 hover:bg-blue-600'
                    }
                    text-white
                  `}
                >
                  {isSavingSocialSecurity ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : socialSecuritySaveSuccess ? (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      <span>Saved!</span>
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      <span>Save Changes</span>
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* 401k Enhancement */}
      <Card className="bg-gray-800 border-gray-700">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-blue-400" />
              <h3 className="text-white text-lg font-semibold">401(k) Optimization</h3>
            </div>
            <Button 
              onClick={() => setShow401kForm(!show401kForm)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {show401kForm ? 'Hide' : 'Configure'}
            </Button>
          </div>

          {show401kForm && (
            <div className="bg-gray-900 p-4 rounded-lg space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-white block mb-2">Employer Match Formula</label>
                  <Input
                    type="text"
                    placeholder="e.g. 100% up to 3%, 50% up to 6%"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={k401Data.match_formula}
                    onChange={(e) => set401kData({...k401Data, match_formula: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-white block mb-2">Vesting Schedule</label>
                  <Input
                    type="text"
                    placeholder="e.g. 25% per year starting year 2"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={k401Data.vesting_schedule}
                    onChange={(e) => set401kData({...k401Data, vesting_schedule: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-white block mb-2">Your Annual Salary</label>
                  <Input
                    type="number"
                    placeholder="e.g. 120000"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={k401Data.employer_contribution}
                    onChange={(e) => set401kData({...k401Data, employer_contribution: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-white block mb-2">Annual 401k Limit (2024)</label>
                  <Input
                    type="number"
                    placeholder="Enter annual 401k contribution limit"
                    className="bg-gray-800 border-gray-600 text-white"
                    value={k401Data.max_contribution}
                    onChange={(e) => set401kData({...k401Data, max_contribution: e.target.value})}
                  />
                </div>
              </div>

              {k401Data.match_formula && k401Data.employer_contribution && (
                <div className="mt-4 p-4 bg-gray-800 rounded-lg">
                  {(() => {
                    const projection = calculate401kProjection();
                    return projection ? (
                      <div>
                        <h4 className="text-white font-medium mb-2">401(k) Match Analysis</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-gray-400">Maximum Annual Match</p>
                            <p className="text-white font-bold">${projection.annualMatch.toLocaleString()}</p>
                          </div>
                          <div>
                            <p className="text-gray-400">Monthly Match Potential</p>
                            <p className="text-white font-bold">${projection.maxMatch.toLocaleString()}</p>
                          </div>
                        </div>
                        {projection.recommendations.length > 0 && (
                          <div className="mt-3 p-3 bg-green-900/30 rounded border border-green-500/20">
                            {projection.recommendations.map((rec, index) => (
                              <p key={index} className="text-green-300 text-sm">{rec}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : null;
                  })()}
                </div>
              )}

              {/* Save Button for 401k */}
              <div className="flex justify-end mt-4 pt-4 border-t border-gray-700">
                <Button
                  onClick={handleSave401k}
                  disabled={isSaving401k}
                  className={`
                    px-4 py-2 font-medium transition-all flex items-center space-x-2
                    ${isSaving401k 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : k401SaveSuccess 
                        ? 'bg-green-500 hover:bg-green-600' 
                        : 'bg-blue-500 hover:bg-blue-600'
                    }
                    text-white
                  `}
                >
                  {isSaving401k ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : k401SaveSuccess ? (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      <span>Saved!</span>
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      <span>Save Changes</span>
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4">
        <Button 
          onClick={loadBenefitsData}
          className="bg-gray-600 hover:bg-gray-700 text-white"
        >
          Refresh Data
        </Button>
      </div>
    </div>
  );
};

export default EnhancedBenefitsManagement;