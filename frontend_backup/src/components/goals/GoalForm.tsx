/**
 * WealthPath AI - Goal Form Component
 * Dynamic form for creating and editing financial goals
 */
import React, { useState, useEffect } from 'react';
import { X, Target, Calendar, DollarSign, Tag, Info } from 'lucide-react';

import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Card from '../ui/Card';
import { useCreateGoalMutation, useUpdateGoalMutation, useCategoriesQuery, useTemplatesQuery } from '../../hooks/use-goal-queries';
import { useFinancialStore } from '../../stores/financial-store';
import { GOAL_CATEGORIES } from '../../types/goals';
import type { Goal, GoalCreate, GoalUpdate } from '../../types/goals';

interface GoalFormProps {
  goal?: Goal; // For editing
  onClose: () => void;
  onSuccess?: () => void;
}

const GoalForm: React.FC<GoalFormProps> = ({ goal, onClose, onSuccess }) => {
  const isEditing = !!goal;
  const financialStore = useFinancialStore();
  const currentNetWorth = financialStore.getNetWorth();
  
  console.log('📝 GoalForm rendered with:', { goal, isEditing });
  console.log('📝 Goal data:', goal);
  console.log('💰 Current net worth from financial store:', currentNetWorth);
  
  // Helper function to get default params for category
  const getDefaultParams = (category: string) => {
    switch (category) {
      case 'retirement':
        return {
          current_age: 30,
          retirement_age: 65,
          annual_spending: 50000
        };
      case 'education':
        return {
          degree_type: 'undergraduate',
          institution_type: 'public',
          start_year: new Date().getFullYear() + 5
        };
      case 'real_estate':
        return {
          property_type: 'primary_residence',
          down_payment_percentage: 20
        };
      case 'emergency_fund':
        return {
          months_of_expenses: 6
        };
      default:
        return {};
    }
  };

  const [formData, setFormData] = useState<GoalCreate>({
    category: goal?.category || 'retirement',
    name: goal?.name || '',
    description: goal?.description || '',
    target_amount: goal?.target_amount || 0,
    target_date: goal?.target_date ? goal.target_date.split('T')[0] : '',
    priority: goal?.priority || 3,
    params: goal?.params || getDefaultParams(goal?.category || 'retirement'),
  });

  // Format number for display in input field
  const formatNumberForInput = (value: number | string) => {
    // Handle string decimals from backend
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    return isNaN(numValue) ? '' : numValue.toString();
  };

  // Format currency for display (with commas, no decimals)
  const formatCurrencyDisplay = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [changeReason, setChangeReason] = useState('');

  // Update form data when goal prop changes (for editing)
  useEffect(() => {
    if (goal) {
      setFormData({
        category: goal.category,
        name: goal.name,
        description: goal.description || '',
        target_amount: goal.target_amount,
        target_date: goal.target_date ? goal.target_date.split('T')[0] : '',
        priority: goal.priority,
        params: goal.params || getDefaultParams(goal.category),
      });
    }
  }, [goal]);

  const { data: categories } = useCategoriesQuery();
  const { data: templates = [] } = useTemplatesQuery();
  const createMutation = useCreateGoalMutation();
  const updateMutation = useUpdateGoalMutation();

  // Filter templates by selected category
  const categoryTemplates = templates.filter(t => t.category === formData.category);

  // Get category info
  const categoryInfo = categories?.[formData.category];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      console.log('Submitting goal with data:', formData);
      
      if (isEditing && goal) {
        const updateData: GoalUpdate = {
          name: formData.name,
          description: formData.description,
          target_amount: formData.target_amount,
          target_date: formData.target_date,
          priority: formData.priority,
          params: formData.params,
          change_reason: changeReason || 'User updated goal',
        };
        
        await updateMutation.mutateAsync({ goalId: goal.goal_id, update: updateData });
      } else {
        await createMutation.mutateAsync(formData);
      }
      
      onSuccess?.();
    } catch (error) {
      console.error('Failed to save goal:', error);
      console.error('Form data at time of error:', formData);
      alert('Failed to save goal. Please try again.');
    }
  };

  const handleTemplateSelect = (templateName: string) => {
    const template = templates.find(t => t.name === templateName);
    if (template) {
      setFormData(prev => ({
        ...prev,
        name: template.name,
        description: template.description,
        category: template.category,
        params: { ...prev.params, ...template.template_params }
      }));
    }
    setSelectedTemplate(templateName);
  };

  const updateParams = (key: string, value: any) => {
    // Don't set NaN values
    if (typeof value === 'number' && isNaN(value)) {
      return;
    }
    
    setFormData(prev => ({
      ...prev,
      params: { ...prev.params, [key]: value }
    }));
  };

  const handleCategoryChange = (category: string) => {
    setFormData(prev => ({
      ...prev,
      category,
      params: getDefaultParams(category)
    }));
  };

  const renderCategorySpecificFields = () => {
    if (!categoryInfo) return null;

    return (
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-white">Category-Specific Information</h4>
        
        {formData.category === 'retirement' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Current Age"
                type="number"
                value={formData.params.current_age || ''}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '') {
                    updateParams('current_age', '');
                  } else {
                    const numValue = parseInt(value);
                    if (!isNaN(numValue)) {
                      updateParams('current_age', numValue);
                    }
                  }
                }}
                min="18"
                max="80"
                required
              />
              <Input
                label="Retirement Age"
                type="number"
                value={formData.params.retirement_age || ''}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '') {
                    updateParams('retirement_age', '');
                  } else {
                    const numValue = parseInt(value);
                    if (!isNaN(numValue)) {
                      updateParams('retirement_age', numValue);
                    }
                  }
                }}
                min="50"
                max="80"
                required
              />
            </div>
            <Input
              label="Annual Spending in Retirement"
              type="number"
              value={formData.params.annual_spending || ''}
              onChange={(e) => {
                const value = e.target.value;
                if (value === '') {
                  updateParams('annual_spending', '');
                } else {
                  const numValue = parseFloat(value);
                  if (!isNaN(numValue)) {
                    updateParams('annual_spending', numValue);
                  }
                }
              }}
              leftIcon={<DollarSign className="w-4 h-4" />}
              min="0"
              required
            />
          </>
        )}

        {formData.category === 'education' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Degree Type"
                value={formData.params.degree_type || ''}
                onChange={(e) => updateParams('degree_type', e.target.value)}
                options={[
                  { value: '', label: 'Select degree type...' },
                  { value: 'undergraduate', label: 'Undergraduate' },
                  { value: 'graduate', label: 'Graduate/Masters' },
                  { value: 'doctoral', label: 'Doctoral/PhD' },
                  { value: 'professional', label: 'Professional (MD, JD, etc.)' },
                  { value: 'certification', label: 'Certification/Training' },
                ]}
                required
              />
              <Select
                label="Institution Type"
                value={formData.params.institution_type || ''}
                onChange={(e) => updateParams('institution_type', e.target.value)}
                options={[
                  { value: '', label: 'Select institution type...' },
                  { value: 'public', label: 'Public University' },
                  { value: 'private', label: 'Private University' },
                  { value: 'community', label: 'Community College' },
                  { value: 'online', label: 'Online Program' },
                  { value: 'trade', label: 'Trade/Technical School' },
                ]}
                required
              />
            </div>
            <Input
              label="Start Year"
              type="number"
              value={formData.params.start_year || ''}
              onChange={(e) => updateParams('start_year', parseInt(e.target.value))}
              min="2024"
              max="2030"
              required
            />
          </>
        )}

        {formData.category === 'real_estate' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Property Type"
                value={formData.params.property_type || ''}
                onChange={(e) => updateParams('property_type', e.target.value)}
                options={[
                  { value: '', label: 'Select property type...' },
                  { value: 'primary_residence', label: 'Primary Residence' },
                  { value: 'investment_property', label: 'Investment Property' },
                  { value: 'vacation_home', label: 'Vacation Home' },
                  { value: 'commercial', label: 'Commercial Property' },
                ]}
                required
              />
              <Input
                label="Down Payment (%)"
                type="number"
                value={formData.params.down_payment_percentage || ''}
                onChange={(e) => updateParams('down_payment_percentage', parseFloat(e.target.value))}
                min="5"
                max="50"
                required
              />
            </div>
          </>
        )}

        {formData.category === 'emergency_fund' && (
          <Input
            label="Months of Expenses"
            type="number"
            value={formData.params.months_of_expenses || ''}
            onChange={(e) => updateParams('months_of_expenses', parseInt(e.target.value))}
            min="3"
            max="12"
            required
          />
        )}
      </div>
    );
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Target className="w-6 h-6 text-white" />
              <h2 className="text-xl font-bold text-white">
                {isEditing ? 'Edit Goal' : 'Create New Goal'}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Goal Type Selection */}
          {!isEditing && (
            <div className="space-y-4">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-white mb-2">Choose Goal Type:</h3>
                <p className="text-gray-400 text-sm">Select the type of goal you want to create</p>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {[
                  { key: 'retirement', emoji: '🏖️', label: 'Retirement', desc: 'FIRE, Early Retirement' },
                  { key: 'real_estate', emoji: '🏠', label: 'Real Estate', desc: 'Home, Investment Property' },
                  { key: 'education', emoji: '🎓', label: 'Education', desc: '529 Plans, College Fund' },
                  { key: 'business', emoji: '🚀', label: 'Business', desc: 'Startup, Investment' },
                  { key: 'custom', emoji: '💰', label: 'Custom', desc: 'Emergency, Vacation, etc.' }
                ].map((goalType) => (
                  <button
                    key={goalType.key}
                    type="button"
                    onClick={() => handleCategoryChange(goalType.key === 'custom' ? 'emergency_fund' : goalType.key)}
                    className={`relative p-4 rounded-lg border-2 transition-all hover:scale-105 ${
                      formData.category === goalType.key || (goalType.key === 'custom' && !['retirement', 'real_estate', 'education', 'business'].includes(formData.category))
                        ? 'border-blue-500 bg-blue-900/30 ring-2 ring-blue-500/50'
                        : 'border-gray-600 bg-gray-700/50 hover:border-blue-400'
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-3xl mb-2">{goalType.emoji}</div>
                      <div className="font-medium text-white text-sm">{goalType.label}</div>
                      <div className="text-xs text-gray-400 mt-1">{goalType.desc}</div>
                    </div>
                    {(formData.category === goalType.key || (goalType.key === 'custom' && !['retirement', 'real_estate', 'education', 'business'].includes(formData.category))) && (
                      <div className="absolute -top-2 -right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">●</span>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Template Selection */}
          {!isEditing && categoryTemplates.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Quick Start Templates for {GOAL_CATEGORIES[formData.category as keyof typeof GOAL_CATEGORIES]}
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {categoryTemplates.map((template) => (
                  <button
                    key={template.name}
                    type="button"
                    onClick={() => handleTemplateSelect(template.name)}
                    className={`text-left p-3 rounded-lg border transition-colors ${
                      selectedTemplate === template.name
                        ? 'border-blue-500 bg-blue-900/20'
                        : 'border-gray-600 bg-gray-700 hover:border-blue-400'
                    }`}
                  >
                    <div className="font-medium text-gray-100">{template.name}</div>
                    <div className="text-sm text-gray-400">{template.description}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Category *"
                value={formData.category}
                onChange={(e) => handleCategoryChange(e.target.value)}
                options={[
                  { value: '', label: 'Select category...' },
                  ...Object.entries(GOAL_CATEGORIES).map(([key, label]) => ({
                    value: key,
                    label
                  }))
                ]}
                leftIcon={<Tag className="w-4 h-4" />}
                required
              />
              
              <Input
                label="Priority (1-10) *"
                type="number"
                value={formData.priority}
                onChange={(e) => setFormData(prev => ({ ...prev, priority: parseInt(e.target.value) }))}
                min="1"
                max="10"
                required
              />
            </div>

            <Input
              label="Goal Name *"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Emergency Fund, House Down Payment"
              required
            />

            <Input
              label="Description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              leftIcon={<Info className="w-4 h-4" />}
              placeholder="Brief description of your goal"
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Input
                  label="Target Amount *"
                  type="number"
                  value={formatNumberForInput(formData.target_amount)}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Handle empty string or invalid input
                    if (value === '' || value === '0') {
                      setFormData(prev => ({ ...prev, target_amount: 0 }));
                    } else {
                      const numValue = parseFloat(value);
                      if (!isNaN(numValue)) {
                        setFormData(prev => ({ ...prev, target_amount: numValue }));
                      }
                    }
                  }}
                  leftIcon={<DollarSign className="w-4 h-4" />}
                  min="100"
                  step="0.01"
                  required
                />
                {formData.target_amount > 0 && (
                  <p className="text-sm text-green-400 mt-1">
                    Formatted: {formatCurrencyDisplay(formData.target_amount)}
                  </p>
                )}
                {!isEditing && currentNetWorth > 0 && (
                  <p className="text-sm text-blue-400 mt-1">
                    💡 Your current net worth: {formatCurrencyDisplay(currentNetWorth)}
                  </p>
                )}
              </div>
              
              <Input
                label="Target Date *"
                type="date"
                value={formData.target_date}
                onChange={(e) => setFormData(prev => ({ ...prev, target_date: e.target.value }))}
                leftIcon={<Calendar className="w-4 h-4" />}
                min={new Date().toISOString().split('T')[0]}
                required
              />
            </div>
          </div>

          {/* Category-specific fields */}
          {renderCategorySpecificFields()}

          {/* Category Information */}
          {categoryInfo && (
            <Card className="bg-blue-900/20 border-blue-600">
              <Card.Body className="p-4">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-400 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-100">{categoryInfo.name} Goals</h4>
                    <p className="text-blue-200 text-sm mt-1">{categoryInfo.description}</p>
                    <p className="text-blue-300 text-xs mt-2">
                      Typical timeline: {categoryInfo.typical_timeline}
                    </p>
                  </div>
                </div>
              </Card.Body>
            </Card>
          )}

          {/* Change reason for edits */}
          {isEditing && (
            <Input
              label="Reason for Change"
              value={changeReason}
              onChange={(e) => setChangeReason(e.target.value)}
              placeholder="Describe why you're making this change..."
            />
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-600">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
              {isLoading ? 'Saving...' : isEditing ? 'Update Goal' : 'Create Goal'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GoalForm;