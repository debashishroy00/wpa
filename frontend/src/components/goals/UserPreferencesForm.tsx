/**
 * WealthPath AI - User Preferences Form Component
 * Form for managing user financial preferences and settings
 */
import React, { useState, useEffect } from 'react';
import { X, Settings, Info, CheckCircle } from 'lucide-react';

import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Card from '../ui/Card';

// Custom Slider Component
interface SliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  leftLabel?: string;
  rightLabel?: string;
  showValue?: boolean;
  formatValue?: (value: number) => string;
}

const Slider: React.FC<SliderProps> = ({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  leftLabel,
  rightLabel,
  showValue = true,
  formatValue
}) => {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-gray-200">{label}</label>
        {showValue && (
          <span className="text-sm text-blue-400 font-medium">
            {formatValue ? formatValue(value) : `${value}/${max}`}
          </span>
        )}
      </div>
      
      {(leftLabel || rightLabel) && (
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>{leftLabel}</span>
          <span>{rightLabel}</span>
        </div>
      )}
      
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
        />
        <style jsx>{`
          .slider::-webkit-slider-thumb {
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #3b82f6;
            cursor: pointer;
            border: 2px solid #1e293b;
          }
          
          .slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #3b82f6;
            cursor: pointer;
            border: 2px solid #1e293b;
          }
        `}</style>
      </div>
    </div>
  );
};
import { 
  useUserPreferencesQuery, 
  useUpdatePreferencesMutation 
} from '../../hooks/use-goal-queries';
import { 
  RISK_TOLERANCE_LEVELS, 
  FINANCIAL_KNOWLEDGE_LEVELS,
  GOAL_CATEGORIES 
} from '../../types/goals';
import type { UserPreferencesUpdate } from '../../types/goals';

interface UserPreferencesFormProps {
  onClose: () => void;
}

const UserPreferencesForm: React.FC<UserPreferencesFormProps> = ({ onClose }) => {
  const { data: preferences, isLoading } = useUserPreferencesQuery();
  const updateMutation = useUpdatePreferencesMutation();

  const [formData, setFormData] = useState<UserPreferencesUpdate>({
    risk_tolerance: 'moderate',
    investment_timeline: 20,
    financial_knowledge: 'intermediate',
    emergency_fund_months: 6,
    debt_payoff_priority: 'balanced',
    goal_categories_enabled: ['retirement', 'emergency_fund', 'education', 'real_estate'],
    notification_preferences: {},
  });

  // Enhanced state for wireframe features
  const [riskTolerance, setRiskTolerance] = useState(7);
  const [investmentStyle, setInvestmentStyle] = useState('aggressive');
  const [assetPreferences, setAssetPreferences] = useState({
    stocks: 8,
    real_estate: 5,
    bonds: 2,
    crypto: 1,
    international: 3
  });
  const [lifestylePrefs, setLifestylePrefs] = useState({
    retirement_lifestyle: 'maintain',
    work_flexibility: {
      part_time: true,
      consulting: true,
      full_retirement: false
    },
    geographic_flexibility: {
      relocate: true,
      stay_current: false,
      international: true
    }
  });
  const [values, setValues] = useState({
    financial_security: 2,
    family_time: 1,
    travel_experiences: 4,
    leaving_legacy: 3,
    luxury_comfort: 5
  });
  const [specialConsiderations, setSpecialConsiderations] = useState({
    esg_investing: true,
    religious_restrictions: false,
    charity_support: true
  });
  
  // Tax preferences state
  const [taxPreferences, setTaxPreferences] = useState({
    tax_filing_status: 'married_filing_jointly',
    federal_tax_bracket: 0.24,
    state_tax_rate: 0.065,
    state: 'NY',
    tax_optimization_priority: 'moderate',
    tax_loss_harvesting: true,
    roth_ira_eligible: true
  });

  const [activeTab, setActiveTab] = useState<'risk' | 'lifestyle' | 'values' | 'goals' | 'tax'>('risk');

  useEffect(() => {
    if (preferences) {
      setFormData({
        risk_tolerance: preferences.risk_tolerance,
        investment_timeline: preferences.investment_timeline,
        financial_knowledge: preferences.financial_knowledge,
        retirement_age: preferences.retirement_age,
        annual_income_goal: preferences.annual_income_goal,
        emergency_fund_months: preferences.emergency_fund_months,
        debt_payoff_priority: preferences.debt_payoff_priority,
        goal_categories_enabled: preferences.goal_categories_enabled,
        notification_preferences: preferences.notification_preferences,
      });

      // Initialize enhanced preferences from database
      if (preferences.risk_score) setRiskTolerance(preferences.risk_score);
      if (preferences.investment_style) setInvestmentStyle(preferences.investment_style);
      if (preferences.stocks_preference) {
        setAssetPreferences(prev => ({
          ...prev,
          stocks: preferences.stocks_preference,
          bonds: preferences.bonds_preference || 5,
          real_estate: preferences.real_estate_preference || 5,
          crypto: preferences.crypto_preference || 1,
          international: prev.international // Keep existing default
        }));
      }
      if (preferences.retirement_lifestyle) {
        setLifestylePrefs(prev => ({
          ...prev,
          retirement_lifestyle: preferences.retirement_lifestyle,
          work_flexibility: preferences.work_flexibility || prev.work_flexibility
        }));
      }
      if (preferences.esg_investing !== undefined) {
        setSpecialConsiderations(prev => ({
          ...prev,
          esg_investing: preferences.esg_investing
        }));
      }
      
      // Initialize tax preferences from database
      if (preferences.tax_filing_status) {
        setTaxPreferences(prev => ({
          ...prev,
          tax_filing_status: preferences.tax_filing_status,
          federal_tax_bracket: preferences.federal_tax_bracket || 0.24,
          state_tax_rate: preferences.state_tax_rate || 0.065,
          state: preferences.state || 'NY',
          tax_optimization_priority: preferences.tax_optimization_priority || 'moderate',
          tax_loss_harvesting: preferences.tax_loss_harvesting !== undefined ? preferences.tax_loss_harvesting : true,
          roth_ira_eligible: preferences.roth_ira_eligible !== undefined ? preferences.roth_ira_eligible : true
        }));
      }
    }
  }, [preferences]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Combine basic formData with enhanced preferences
      const enhancedPreferences = {
        ...formData,
        risk_score: riskTolerance,
        investment_style: investmentStyle,
        stocks_preference: assetPreferences.stocks,
        bonds_preference: assetPreferences.bonds,
        real_estate_preference: assetPreferences.real_estate,
        crypto_preference: assetPreferences.crypto,
        retirement_lifestyle: lifestylePrefs.retirement_lifestyle,
        work_flexibility: lifestylePrefs.work_flexibility,
        esg_investing: specialConsiderations.esg_investing,
        ...taxPreferences
      };
      
      await updateMutation.mutateAsync(enhancedPreferences);
      onClose();
    } catch (error) {
      console.error('Failed to update preferences:', error);
      alert('Failed to update preferences. Please try again.');
    }
  };

  const handleCategoryToggle = (category: string) => {
    const current = formData.goal_categories_enabled || [];
    const updated = current.includes(category)
      ? current.filter(c => c !== category)
      : [...current, category];
    
    setFormData(prev => ({ ...prev, goal_categories_enabled: updated }));
  };

  const handleNotificationToggle = (key: string) => {
    const current = formData.notification_preferences || {};
    setFormData(prev => ({
      ...prev,
      notification_preferences: {
        ...current,
        [key]: !current[key]
      }
    }));
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-xl p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 to-blue-600 p-6 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Settings className="w-6 h-6 text-white" />
              <h2 className="text-xl font-bold text-white">Financial Preferences</h2>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-700">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'risk', label: 'Risk & Investment' },
              { id: 'lifestyle', label: 'Lifestyle' },
              { id: 'values', label: 'Values & Priorities' },
              { id: 'goals', label: 'Goal Categories' },
              { id: 'tax', label: 'Tax & Optimization' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          {activeTab === 'risk' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Risk & Investment Profile</h3>
              
              {/* Overall Risk Tolerance */}
              <div className="space-y-4">
                <Slider
                  label="Overall Risk Tolerance"
                  value={riskTolerance}
                  onChange={setRiskTolerance}
                  min={1}
                  max={10}
                  leftLabel="Conservative"
                  rightLabel="Aggressive"
                  formatValue={(v) => `${v}/10 - ${v >= 8 ? 'Aggressive' : v >= 5 ? 'Moderate-High' : 'Conservative'}`}
                />
              </div>

              {/* Investment Style */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-200">Investment Style</label>
                <div className="space-y-2">
                  {[
                    { value: 'conservative', label: 'Conservative (Preserve capital)' },
                    { value: 'moderate', label: 'Moderate (Balanced growth)' },
                    { value: 'aggressive', label: 'Aggressive (Maximum growth)' }
                  ].map((option) => (
                    <label key={option.value} className="flex items-center space-x-3">
                      <input
                        type="radio"
                        name="investmentStyle"
                        value={option.value}
                        checked={investmentStyle === option.value}
                        onChange={(e) => setInvestmentStyle(e.target.value)}
                        className="h-4 w-4 text-blue-600"
                      />
                      <span className="text-gray-300">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Asset Preferences */}
              <div className="space-y-4">
                <h4 className="font-medium text-gray-200">Asset Preferences</h4>
                <div className="space-y-3">
                  {[
                    { key: 'stocks', label: 'Stocks' },
                    { key: 'real_estate', label: 'Real Estate' },
                    { key: 'bonds', label: 'Bonds' },
                    { key: 'crypto', label: 'Crypto' },
                    { key: 'international', label: 'International' }
                  ].map((asset) => (
                    <Slider
                      key={asset.key}
                      label={asset.label}
                      value={assetPreferences[asset.key as keyof typeof assetPreferences]}
                      onChange={(value) => setAssetPreferences(prev => ({ ...prev, [asset.key]: value }))}
                      min={1}
                      max={10}
                      formatValue={(v) => `${v}/10 - ${v >= 8 ? 'High' : v >= 5 ? 'Medium' : v === 1 ? 'None' : 'Low'}`}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'lifestyle' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Lifestyle Preferences</h3>
              
              {/* Retirement Lifestyle */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-200">Retirement Lifestyle</label>
                <div className="space-y-2">
                  {[
                    { value: 'downsize', label: 'Downsize (Reduce expenses by 30%)' },
                    { value: 'maintain', label: 'Maintain (Same as current)' },
                    { value: 'upgrade', label: 'Upgrade (Increase by 20%)' }
                  ].map((option) => (
                    <label key={option.value} className="flex items-center space-x-3">
                      <input
                        type="radio"
                        name="retirementLifestyle"
                        value={option.value}
                        checked={lifestylePrefs.retirement_lifestyle === option.value}
                        onChange={(e) => setLifestylePrefs(prev => ({ ...prev, retirement_lifestyle: e.target.value }))}
                        className="h-4 w-4 text-blue-600"
                      />
                      <span className="text-gray-300">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Work Flexibility */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-200">Work Flexibility</label>
                <div className="space-y-2">
                  {[
                    { key: 'part_time', label: 'Open to part-time work in retirement' },
                    { key: 'consulting', label: 'Consider consulting/freelance' },
                    { key: 'full_retirement', label: 'Full retirement only' }
                  ].map((option) => (
                    <label key={option.key} className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={lifestylePrefs.work_flexibility[option.key as keyof typeof lifestylePrefs.work_flexibility]}
                        onChange={(e) => setLifestylePrefs(prev => ({
                          ...prev,
                          work_flexibility: { ...prev.work_flexibility, [option.key]: e.target.checked }
                        }))}
                        className="h-4 w-4 text-blue-600 rounded"
                      />
                      <span className="text-gray-300">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Geographic Flexibility */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-200">Geographic Flexibility</label>
                <div className="space-y-2">
                  {[
                    { key: 'relocate', label: 'Willing to relocate for lower cost of living' },
                    { key: 'stay_current', label: 'Must stay in current area' },
                    { key: 'international', label: 'Open to international retirement' }
                  ].map((option) => (
                    <label key={option.key} className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={lifestylePrefs.geographic_flexibility[option.key as keyof typeof lifestylePrefs.geographic_flexibility]}
                        onChange={(e) => setLifestylePrefs(prev => ({
                          ...prev,
                          geographic_flexibility: { ...prev.geographic_flexibility, [option.key]: e.target.checked }
                        }))}
                        className="h-4 w-4 text-blue-600 rounded"
                      />
                      <span className="text-gray-300">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'values' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Values & Priorities</h3>
              
              {/* Priority Ranking */}
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-200 mb-3">What matters most? (Rank 1-5)</h4>
                  <div className="space-y-3">
                    {[
                      { key: 'financial_security', label: 'Financial Security' },
                      { key: 'family_time', label: 'Family Time' },
                      { key: 'travel_experiences', label: 'Travel & Experiences' },
                      { key: 'leaving_legacy', label: 'Leaving a Legacy' },
                      { key: 'luxury_comfort', label: 'Luxury & Comfort' }
                    ].map((value) => (
                      <div key={value.key} className="flex items-center justify-between">
                        <span className="text-gray-300">{value.label}</span>
                        <select
                          value={values[value.key as keyof typeof values]}
                          onChange={(e) => setValues(prev => ({ ...prev, [value.key]: parseInt(e.target.value) }))}
                          className="bg-gray-700 text-white border border-gray-600 rounded px-2 py-1 text-sm"
                        >
                          {[1, 2, 3, 4, 5].map(num => (
                            <option key={num} value={num}>{num}</option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Special Considerations */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-200">Special Considerations</label>
                <div className="space-y-2">
                  {[
                    { key: 'esg_investing', label: 'ESG/Sustainable Investing Important' },
                    { key: 'religious_restrictions', label: 'Religious/Ethical Restrictions' },
                    { key: 'charity_support', label: 'Want to support charities' }
                  ].map((option) => (
                    <label key={option.key} className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={specialConsiderations[option.key as keyof typeof specialConsiderations]}
                        onChange={(e) => setSpecialConsiderations(prev => ({ ...prev, [option.key]: e.target.checked }))}
                        className="h-4 w-4 text-blue-600 rounded"
                      />
                      <span className="text-gray-300">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'goals' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Financial Profile</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <Select
                    label="Risk Tolerance"
                    value={formData.risk_tolerance || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, risk_tolerance: e.target.value }))}
                    options={[
                      ...Object.entries(RISK_TOLERANCE_LEVELS).map(([key, label]) => ({
                        value: key,
                        label
                      }))
                    ]}
                  />
                  
                  <Select
                    label="Financial Knowledge"
                    value={formData.financial_knowledge || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, financial_knowledge: e.target.value }))}
                    options={[
                      ...Object.entries(FINANCIAL_KNOWLEDGE_LEVELS).map(([key, label]) => ({
                        value: key,
                        label
                      }))
                    ]}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <Input
                    label="Investment Timeline (years)"
                    type="number"
                    value={formData.investment_timeline || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, investment_timeline: parseInt(e.target.value) }))}
                    min="1"
                    max="50"
                  />
                  
                  <Input
                    label="Emergency Fund (months of expenses)"
                    type="number"
                    value={formData.emergency_fund_months || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, emergency_fund_months: parseInt(e.target.value) }))}
                    min="1"
                    max="12"
                  />
                </div>

                <Select
                  label="Debt Payoff Strategy"
                  value={formData.debt_payoff_priority || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, debt_payoff_priority: e.target.value }))}
                  options={[
                    { value: 'avalanche', label: 'Avalanche (Highest Interest First)' },
                    { value: 'snowball', label: 'Snowball (Smallest Balance First)' },
                    { value: 'balanced', label: 'Balanced Approach' },
                  ]}
                />
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Optional Goals</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Retirement Age"
                    type="number"
                    value={formData.retirement_age || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, retirement_age: parseInt(e.target.value) || undefined }))}
                    min="50"
                    max="80"
                    placeholder="e.g., 65"
                  />
                  
                  <Input
                    label="Annual Income Goal"
                    type="number"
                    value={formData.annual_income_goal || ''}
                    onChange={(e) => setFormData(prev => ({ ...prev, annual_income_goal: parseFloat(e.target.value) || undefined }))}
                    min="0"
                    step="1000"
                    placeholder="e.g., 100000"
                  />
                </div>
              </div>

              <Card className="bg-blue-900/20 border-blue-600">
                <Card.Body className="p-4">
                  <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-blue-400 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-blue-100">About These Settings</h4>
                      <p className="text-blue-200 text-sm mt-1">
                        These preferences help us provide personalized recommendations and goal templates 
                        that match your financial situation and risk tolerance.
                      </p>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </div>
          )}

          {activeTab === 'goals' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Enabled Goal Categories</h3>
                <p className="text-gray-400 text-sm mb-4">
                  Select which types of goals you want to track. You can change this anytime.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(GOAL_CATEGORIES).map(([key, label]) => (
                    <div
                      key={key}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        formData.goal_categories_enabled?.includes(key)
                          ? 'border-blue-500 bg-blue-900/20'
                          : 'border-gray-600 bg-gray-700 hover:border-gray-500'
                      }`}
                      onClick={() => handleCategoryToggle(key)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium text-white">{label}</h4>
                          <p className="text-gray-400 text-xs">
                            {key === 'retirement' && 'Long-term retirement planning'}
                            {key === 'education' && 'Education and learning goals'}
                            {key === 'real_estate' && 'Property and real estate'}
                            {key === 'business' && 'Business and entrepreneurship'}
                            {key === 'travel' && 'Travel and experiences'}
                            {key === 'emergency_fund' && 'Emergency savings'}
                            {key === 'debt_payoff' && 'Debt elimination'}
                            {key === 'major_purchase' && 'Large purchases'}
                            {key === 'other' && 'Custom and other goals'}
                          </p>
                        </div>
                        {formData.goal_categories_enabled?.includes(key) && (
                          <CheckCircle className="w-5 h-5 text-blue-500" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tax' && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white mb-4">Tax & Optimization</h3>
              
              {/* Tax Filing Status */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-200">Tax Filing Status</label>
                <select
                  value={taxPreferences.tax_filing_status}
                  onChange={(e) => setTaxPreferences(prev => ({ ...prev, tax_filing_status: e.target.value }))}
                  className="w-full p-2 bg-gray-700 text-white border border-gray-600 rounded"
                >
                  <option value="single">Single</option>
                  <option value="married_filing_jointly">Married Filing Jointly</option>
                  <option value="married_filing_separately">Married Filing Separately</option>
                  <option value="head_of_household">Head of Household</option>
                  <option value="qualifying_widow">Qualifying Widow(er)</option>
                </select>
              </div>

              {/* Tax Brackets */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium text-gray-200">Federal Tax Bracket</label>
                  <select
                    value={taxPreferences.federal_tax_bracket}
                    onChange={(e) => setTaxPreferences(prev => ({ ...prev, federal_tax_bracket: parseFloat(e.target.value) }))}
                    className="w-full p-2 bg-gray-700 text-white border border-gray-600 rounded mt-2"
                  >
                    <option value={0.10}>10%</option>
                    <option value={0.12}>12%</option>
                    <option value={0.22}>22%</option>
                    <option value={0.24}>24%</option>
                    <option value={0.32}>32%</option>
                    <option value={0.35}>35%</option>
                    <option value={0.37}>37%</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-200">State</label>
                  <input
                    type="text"
                    value={taxPreferences.state}
                    onChange={(e) => setTaxPreferences(prev => ({ ...prev, state: e.target.value.toUpperCase() }))}
                    maxLength={2}
                    placeholder="NY"
                    className="w-full p-2 bg-gray-700 text-white border border-gray-600 rounded mt-2"
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-200">State Tax Rate (%)</label>
                <input
                  type="number"
                  value={(taxPreferences.state_tax_rate * 100).toFixed(2)}
                  onChange={(e) => setTaxPreferences(prev => ({ ...prev, state_tax_rate: parseFloat(e.target.value) / 100 }))}
                  min="0"
                  max="15"
                  step="0.1"
                  className="w-full p-2 bg-gray-700 text-white border border-gray-600 rounded mt-2"
                />
              </div>

              {/* Tax Optimization */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-200">Tax Optimization Priority</label>
                <div className="space-y-2">
                  {[
                    { value: 'aggressive', label: 'Aggressive (Maximum tax savings)' },
                    { value: 'moderate', label: 'Moderate (Balanced approach)' },
                    { value: 'conservative', label: 'Conservative (Simple strategies)' },
                    { value: 'none', label: 'None (No tax optimization)' }
                  ].map((option) => (
                    <label key={option.value} className="flex items-center space-x-3">
                      <input
                        type="radio"
                        name="taxOptimization"
                        value={option.value}
                        checked={taxPreferences.tax_optimization_priority === option.value}
                        onChange={(e) => setTaxPreferences(prev => ({ ...prev, tax_optimization_priority: e.target.value }))}
                        className="h-4 w-4 text-blue-600"
                      />
                      <span className="text-gray-300">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Tax Strategies */}
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-200">Tax Strategies</label>
                <div className="space-y-2">
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={taxPreferences.tax_loss_harvesting}
                      onChange={(e) => setTaxPreferences(prev => ({ ...prev, tax_loss_harvesting: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                    <span className="text-gray-300">Tax Loss Harvesting</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={taxPreferences.roth_ira_eligible}
                      onChange={(e) => setTaxPreferences(prev => ({ ...prev, roth_ira_eligible: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 rounded"
                    />
                    <span className="text-gray-300">Roth IRA Eligible</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Notification Preferences</h3>
                <p className="text-gray-400 text-sm mb-4">
                  Choose how you'd like to be notified about your goal progress and milestones.
                </p>
                
                <div className="space-y-4">
                  {[
                    { key: 'goal_reminders', label: 'Goal Progress Reminders', description: 'Weekly reminders to update your progress' },
                    { key: 'milestone_alerts', label: 'Milestone Achievements', description: 'Notifications when you reach milestones' },
                    { key: 'deadline_warnings', label: 'Deadline Warnings', description: 'Alerts for upcoming goal deadlines' },
                    { key: 'conflict_alerts', label: 'Goal Conflict Alerts', description: 'Notifications about conflicting goals' },
                    { key: 'monthly_summary', label: 'Monthly Summary', description: 'Monthly progress summary email' },
                  ].map((notification) => (
                    <div
                      key={notification.key}
                      className="flex items-center justify-between p-4 bg-gray-700 rounded-lg"
                    >
                      <div>
                        <h4 className="font-medium text-white">{notification.label}</h4>
                        <p className="text-gray-400 text-sm">{notification.description}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleNotificationToggle(notification.key)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          formData.notification_preferences?.[notification.key]
                            ? 'bg-blue-600'
                            : 'bg-gray-600'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            formData.notification_preferences?.[notification.key]
                              ? 'translate-x-6'
                              : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-600 mt-8">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={updateMutation.isPending}
              className="bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
            >
              {updateMutation.isPending ? 'Saving...' : 'Save Preferences'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserPreferencesForm;