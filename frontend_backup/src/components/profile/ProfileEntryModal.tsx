/**
 * WealthPath AI - Profile Entry Modal
 * Dedicated modal for adding/editing profile, family, benefits, and tax data
 */
import React, { useState, useEffect } from 'react';
import { X, User, Users, Heart, FileText, Calendar } from 'lucide-react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { profileApi } from '../../utils/profile-api';

interface ProfileEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  editingItem?: any;
}

interface FormData {
  type: 'profile' | 'family' | 'benefit' | 'tax';
  [key: string]: any;
}

const ProfileEntryModal: React.FC<ProfileEntryModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  editingItem
}) => {
  const [formData, setFormData] = useState<FormData>({
    type: 'profile'
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize form data when modal opens or editing item changes
  useEffect(() => {
    if (isOpen && editingItem) {
      setFormData({
        type: editingItem.type,
        ...editingItem
      });
    } else if (isOpen) {
      setFormData({
        type: 'profile'
      });
    }
  }, [isOpen, editingItem]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const { type, ...data } = formData;
      
      switch (type) {
        case 'profile':
          if (editingItem?.id) {
            await profileApi.updateProfile(data);
          } else {
            await profileApi.createOrUpdateProfile(data);
          }
          break;
          
        case 'family':
          if (editingItem?.id) {
            await profileApi.updateFamilyMember(editingItem.id, data);
          } else {
            await profileApi.addFamilyMember(data);
          }
          break;
          
        case 'benefit':
          if (editingItem?.id) {
            await profileApi.updateBenefit(editingItem.id, data);
          } else {
            await profileApi.addBenefit(data);
          }
          break;
          
        case 'tax':
          if (editingItem?.id) {
            await profileApi.updateTaxInfo(editingItem.id, data);
          } else {
            await profileApi.addTaxInfo(data);
          }
          break;
      }

      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Failed to save:', error);
      alert(`Failed to save: ${error.message || 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (!isOpen) return null;

  const getModalTitle = () => {
    const action = editingItem?.id ? 'Edit' : 'Add';
    switch (formData.type) {
      case 'profile': return `${action} Personal Information`;
      case 'family': return `${action} Family Member`;
      case 'benefit': return `${action} Benefit`;
      case 'tax': return `${action} Tax Information`;
      default: return `${action} Entry`;
    }
  };

  const getModalIcon = () => {
    switch (formData.type) {
      case 'profile': return <User className="w-6 h-6 text-blue-400" />;
      case 'family': return <Users className="w-6 h-6 text-green-400" />;
      case 'benefit': return <Heart className="w-6 h-6 text-purple-400" />;
      case 'tax': return <FileText className="w-6 h-6 text-orange-400" />;
      default: return <User className="w-6 h-6 text-blue-400" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getModalIcon()}
              <h2 className="text-xl font-bold text-white">
                {getModalTitle()}
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

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Type Selection - only show for new entries */}
          {!editingItem?.id && (
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-1">
                Entry Type
              </label>
              <Select
                value={formData.type}
                onChange={(e) => setFormData({ type: e.target.value as any })}
                options={[
                  { value: 'profile', label: 'Personal Information' },
                  { value: 'family', label: 'Family Member' },
                  { value: 'benefit', label: 'Benefit' },
                  { value: 'tax', label: 'Tax Information' },
                ]}
              />
            </div>
          )}

          {/* Profile Fields */}
          {formData.type === 'profile' && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Age"
                  type="number"
                  value={formData.age || ''}
                  onChange={(e) => handleInputChange('age', e.target.value ? parseInt(e.target.value) : null)}
                  placeholder="35"
                />
                <Input
                  label="Date of Birth"
                  type="date"
                  value={formData.date_of_birth ? formData.date_of_birth.split('T')[0] : ''}
                  onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
                />
                <Input
                  label="State"
                  type="text"
                  value={formData.state || ''}
                  onChange={(e) => handleInputChange('state', e.target.value)}
                  placeholder="California"
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Select
                  label="Marital Status"
                  value={formData.marital_status || ''}
                  onChange={(e) => handleInputChange('marital_status', e.target.value)}
                  options={[
                    { value: '', label: 'Select...' },
                    { value: 'single', label: 'Single' },
                    { value: 'married', label: 'Married' },
                    { value: 'divorced', label: 'Divorced' },
                    { value: 'widowed', label: 'Widowed' },
                  ]}
                />
                <Select
                  label="Employment Status"
                  value={formData.employment_status || ''}
                  onChange={(e) => handleInputChange('employment_status', e.target.value)}
                  options={[
                    { value: '', label: 'Select...' },
                    { value: 'employed', label: 'Employed' },
                    { value: 'self_employed', label: 'Self Employed' },
                    { value: 'unemployed', label: 'Unemployed' },
                    { value: 'retired', label: 'Retired' },
                    { value: 'student', label: 'Student' },
                  ]}
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Occupation"
                  type="text"
                  value={formData.occupation || ''}
                  onChange={(e) => handleInputChange('occupation', e.target.value)}
                  placeholder="Software Engineer"
                />
                <Select
                  label="Risk Tolerance"
                  value={formData.risk_tolerance || ''}
                  onChange={(e) => handleInputChange('risk_tolerance', e.target.value)}
                  options={[
                    { value: '', label: 'Select...' },
                    { value: 'conservative', label: 'Conservative' },
                    { value: 'moderate', label: 'Moderate' },
                    { value: 'aggressive', label: 'Aggressive' },
                  ]}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-1">
                  Additional Notes
                </label>
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Any additional personal information..."
                  className="w-full p-3 border border-gray-600 bg-gray-700 text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                />
              </div>
            </>
          )}

          {/* Family Member Fields */}
          {formData.type === 'family' && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Name"
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="John Doe"
                  required
                />
                <Select
                  label="Relationship"
                  value={formData.relationship_type || ''}
                  onChange={(e) => handleInputChange('relationship_type', e.target.value)}
                  options={[
                    { value: '', label: 'Select...' },
                    { value: 'spouse', label: 'Spouse' },
                    { value: 'partner', label: 'Partner' },
                    { value: 'child', label: 'Child' },
                    { value: 'dependent', label: 'Dependent' },
                    { value: 'parent', label: 'Parent' },
                    { value: 'sibling', label: 'Sibling' },
                    { value: 'other', label: 'Other' },
                  ]}
                  required
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Age"
                  type="number"
                  value={formData.age || ''}
                  onChange={(e) => handleInputChange('age', e.target.value ? parseInt(e.target.value) : null)}
                  placeholder="35"
                />
                <Input
                  label="Date of Birth"
                  type="date"
                  value={formData.date_of_birth ? formData.date_of_birth.split('T')[0] : ''}
                  onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Annual Income"
                  type="number"
                  value={formData.income || ''}
                  onChange={(e) => handleInputChange('income', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="50000"
                />
                <Input
                  label="Retirement Savings"
                  type="number"
                  value={formData.retirement_savings || ''}
                  onChange={(e) => handleInputChange('retirement_savings', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="100000"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-1">
                  Notes
                </label>
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Additional information about family member..."
                  className="w-full p-3 border border-gray-600 bg-gray-700 text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                />
              </div>
            </>
          )}

          {/* Benefit Fields */}
          {formData.type === 'benefit' && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Benefit Name"
                  type="text"
                  value={formData.benefit_name || ''}
                  onChange={(e) => handleInputChange('benefit_name', e.target.value)}
                  placeholder="Social Security"
                  required
                />
                <Select
                  label="Benefit Type"
                  value={formData.benefit_type || ''}
                  onChange={(e) => handleInputChange('benefit_type', e.target.value)}
                  options={[
                    { value: '', label: 'Select...' },
                    { value: 'social_security', label: 'Social Security' },
                    { value: 'pension', label: 'Pension' },
                    { value: 'disability', label: 'Disability' },
                    { value: 'unemployment', label: 'Unemployment' },
                    { value: 'health_insurance', label: 'Health Insurance' },
                    { value: 'other', label: 'Other' },
                  ]}
                  required
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Monthly Benefit Amount"
                  type="number"
                  value={formData.estimated_monthly_benefit || ''}
                  onChange={(e) => handleInputChange('estimated_monthly_benefit', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="2500"
                />
                <Input
                  label="Eligibility Date"
                  type="date"
                  value={formData.eligibility_date ? formData.eligibility_date.split('T')[0] : ''}
                  onChange={(e) => handleInputChange('eligibility_date', e.target.value)}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-1">
                  Notes
                </label>
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Additional benefit details..."
                  className="w-full p-3 border border-gray-600 bg-gray-700 text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                />
              </div>
            </>
          )}

          {/* Tax Information Fields */}
          {formData.type === 'tax' && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Tax Year"
                  type="number"
                  value={formData.tax_year || new Date().getFullYear()}
                  onChange={(e) => handleInputChange('tax_year', e.target.value ? parseInt(e.target.value) : null)}
                  placeholder="2024"
                  required
                />
                <Select
                  label="Filing Status"
                  value={formData.filing_status || ''}
                  onChange={(e) => handleInputChange('filing_status', e.target.value)}
                  options={[
                    { value: '', label: 'Select...' },
                    { value: 'single', label: 'Single' },
                    { value: 'married_jointly', label: 'Married Filing Jointly' },
                    { value: 'married_separately', label: 'Married Filing Separately' },
                    { value: 'head_of_household', label: 'Head of Household' },
                    { value: 'qualifying_widow', label: 'Qualifying Widow(er)' },
                  ]}
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Adjusted Gross Income"
                  type="number"
                  value={formData.adjusted_gross_income || ''}
                  onChange={(e) => handleInputChange('adjusted_gross_income', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="75000"
                />
                <Input
                  label="Federal Tax Bracket (%)"
                  type="number"
                  step="0.1"
                  value={formData.federal_tax_bracket || ''}
                  onChange={(e) => handleInputChange('federal_tax_bracket', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="22"
                />
                <Input
                  label="Effective Tax Rate (%)"
                  type="number"
                  step="0.1"
                  value={formData.effective_tax_rate || ''}
                  onChange={(e) => handleInputChange('effective_tax_rate', e.target.value ? parseFloat(e.target.value) : null)}
                  placeholder="18.5"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-200 mb-1">
                  Notes
                </label>
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Additional tax information..."
                  className="w-full p-3 border border-gray-600 bg-gray-700 text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3}
                />
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-600">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
              {isSubmitting ? 'Saving...' : (editingItem?.id ? 'Update' : 'Save')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileEntryModal;