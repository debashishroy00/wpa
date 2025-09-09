/**
 * WealthPath AI - Smart Entry Modal
 * Architecture Lead Directive: Smart suggestions and category-aware entry form
 */
import React, { useState, useEffect } from 'react';
import { X, DollarSign, Calendar, FileText, Lightbulb } from 'lucide-react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import { EntryCategory, FrequencyType, FinancialEntryCreate } from '../../types/financial';
import { useCreateFinancialEntryMutation } from '../../hooks/use-financial-queries';
import { useCreateProfileEntryMutation } from '../../hooks/use-profile-queries';
import SmartLiabilityForm from './LiabilityForms/SmartLiabilityForm';

interface SmartEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  category?: EntryCategory;
  subcategory?: string;
  onSuccess?: () => void;
  editingEntry?: any; // For editing existing entries including profile entries
}

// Smart suggestions based on category
const SMART_SUGGESTIONS = {
  [EntryCategory.ASSETS]: {
    'Cash & Bank Accounts': [
      { name: 'Checking Account', avgValue: 3000, description: 'Primary checking account', cash_percentage: 100 },
      { name: 'Savings Account', avgValue: 50000, description: 'Emergency fund and savings', cash_percentage: 100 },
      { name: 'Money Market Account', avgValue: 67000, description: 'High-yield savings account', cash_percentage: 100 },
      { name: 'Checking Offshore', avgValue: 5681, description: 'Offshore bank account', cash_percentage: 100 },
      { name: 'Certificate of Deposit', avgValue: 10000, description: 'Fixed-term deposit', cash_percentage: 100 }
    ],
    'Investment Accounts': [
      { name: 'Brokerage Account', avgValue: 100000, description: 'Taxable investment account', stocks_percentage: 70, bonds_percentage: 15, cash_percentage: 10, real_estate_percentage: 5 },
      { name: 'Individual Stocks', avgValue: 25000, description: 'Direct stock holdings', stocks_percentage: 100 },
      { name: 'ETF Portfolio', avgValue: 50000, description: 'Exchange-traded funds', stocks_percentage: 80, bonds_percentage: 20 },
      { name: 'Mutual Funds', avgValue: 75000, description: 'Managed investment funds', stocks_percentage: 60, bonds_percentage: 30, real_estate_percentage: 10 }
    ],
    'Retirement Accounts': [
      { name: '401k Account', avgValue: 150000, description: 'Employer-sponsored retirement', stocks_percentage: 60, bonds_percentage: 30, real_estate_percentage: 10 },
      { name: 'Traditional IRA', avgValue: 75000, description: 'Traditional individual retirement', stocks_percentage: 65, bonds_percentage: 35 },
      { name: 'Roth IRA', avgValue: 50000, description: 'After-tax retirement account', stocks_percentage: 70, bonds_percentage: 20, real_estate_percentage: 10 },
      { name: 'SEP-IRA', avgValue: 100000, description: 'Self-employed retirement', stocks_percentage: 55, bonds_percentage: 35, real_estate_percentage: 10 }
    ],
    'Real Estate': [
      { name: 'Primary Residence', avgValue: 450000, description: 'Your main home', real_estate_percentage: 100 },
      { name: 'Rental Property', avgValue: 300000, description: 'Investment rental property', real_estate_percentage: 100 },
      { name: 'Vacation Home', avgValue: 250000, description: 'Second home or vacation property', real_estate_percentage: 100 }
    ],
    'Personal Property': [
      { name: 'Jewelry', avgValue: 30000, description: 'Valuable jewelry and watches', alternative_percentage: 100 },
      { name: 'Art & Collectibles', avgValue: 25000, description: 'Art, antiques, collectibles', alternative_percentage: 100 },
      { name: 'Vehicles', avgValue: 35000, description: 'Cars, boats, motorcycles', alternative_percentage: 100 },
      { name: 'Electronics', avgValue: 5000, description: 'Computers, phones, gadgets' },
      { name: 'Furniture', avgValue: 15000, description: 'Home furniture and fixtures' }
    ],
    'Business Assets': [
      { name: 'Business Checking', avgValue: 25000, description: 'Business bank account' },
      { name: 'Business Equipment', avgValue: 50000, description: 'Machinery, computers, tools' },
      { name: 'Business Real Estate', avgValue: 500000, description: 'Commercial property' },
      { name: 'Business Investments', avgValue: 100000, description: 'Business-owned investments' }
    ]
  },
  [EntryCategory.LIABILITIES]: {
    'Mortgage & Real Estate': [
      { name: 'Primary Mortgage', avgValue: 350000, description: 'Home loan balance' },
      { name: 'Investment Property Loan', avgValue: 200000, description: 'Rental property mortgage' },
      { name: 'HELOC', avgValue: 50000, description: 'Home equity line of credit' }
    ],
    'Credit Cards': [
      { name: 'Personal Credit Card', avgValue: 5000, description: 'Credit card balance' },
      { name: 'Business Credit Card', avgValue: 8000, description: 'Business expenses card' }
    ]
  },
  [EntryCategory.INCOME]: {
    'Employment Income': [
      { name: 'Base Salary', avgValue: 8000, description: 'Monthly salary', frequency: FrequencyType.MONTHLY },
      { name: 'Annual Bonus', avgValue: 15000, description: 'Year-end bonus', frequency: FrequencyType.ANNUALLY },
      { name: 'Stock Options', avgValue: 25000, description: 'Equity compensation', frequency: FrequencyType.ANNUALLY }
    ],
    'Investment Income': [
      { name: 'Dividend Income', avgValue: 500, description: 'Stock dividends', frequency: FrequencyType.MONTHLY },
      { name: 'Rental Income', avgValue: 2500, description: 'Property rental', frequency: FrequencyType.MONTHLY },
      { name: 'Interest Income', avgValue: 200, description: 'Savings interest', frequency: FrequencyType.MONTHLY }
    ]
  },
  [EntryCategory.EXPENSES]: {
    'Housing': [
      { name: 'Mortgage Payment', avgValue: 2500, description: 'Monthly mortgage', frequency: FrequencyType.MONTHLY },
      { name: 'Property Tax', avgValue: 8000, description: 'Annual property tax', frequency: FrequencyType.ANNUALLY },
      { name: 'Utilities', avgValue: 200, description: 'Electric, gas, water', frequency: FrequencyType.MONTHLY }
    ],
    'Transportation': [
      { name: 'Car Payment', avgValue: 400, description: 'Auto loan payment', frequency: FrequencyType.MONTHLY },
      { name: 'Gas', avgValue: 150, description: 'Fuel costs', frequency: FrequencyType.MONTHLY },
      { name: 'Car Insurance', avgValue: 1200, description: 'Auto insurance', frequency: FrequencyType.ANNUALLY }
    ]
  }
};

// Helper function to get subcategory options based on category
const getSubcategoryOptions = (category: EntryCategory) => {
  const options = {
    [EntryCategory.PROFILE]: [
      { value: '', label: 'Select subcategory...' },
      { value: 'Personal Information', label: 'Personal Information' },
      { value: 'Spouse/Partner', label: 'Spouse/Partner' },
      { value: 'Dependents', label: 'Dependents' },
      { value: 'Extended Family', label: 'Extended Family' },
      { value: 'Contact & Location', label: 'Contact & Location' },
    ],
    [EntryCategory.BENEFITS]: [
      { value: '', label: 'Select subcategory...' },
      { value: 'social_security', label: 'Social Security' },
      { value: 'employment_benefits', label: 'Employment Benefits' },
      { value: 'government_benefits', label: 'Government Benefits' },
    ],
    [EntryCategory.TAX_INFO]: [
      { value: '', label: 'Select subcategory...' },
      { value: 'filing_status', label: 'Filing Status' },
      { value: 'tax_advantaged', label: 'Tax Advantaged Accounts' },
      { value: 'tax_planning', label: 'Tax Planning' },
    ],
    [EntryCategory.ASSETS]: [
      { value: '', label: 'Select subcategory...' },
      { value: 'cash_bank_accounts', label: 'Cash & Bank Accounts' },
      { value: 'investment_accounts', label: 'Investment Accounts' },
      { value: 'retirement_accounts', label: 'Retirement Accounts' },
      { value: 'real_estate', label: 'Real Estate' },
      { value: 'personal_property', label: 'Personal Property' },
      { value: 'business_assets', label: 'Business Assets' },
      { value: 'other_assets', label: 'Other Assets' },
    ],
    [EntryCategory.LIABILITIES]: [
      { value: '', label: 'Select subcategory...' },
      { value: 'mortgage_real_estate', label: 'Mortgage & Real Estate' },
      { value: 'credit_cards', label: 'Credit Cards' },
      { value: 'auto_loans', label: 'Auto Loans' },
      { value: 'student_loans', label: 'Student Loans' },
      { value: 'personal_loans', label: 'Personal Loans' },
      { value: 'other_debt', label: 'Other Debt' },
    ],
    [EntryCategory.INCOME]: [
      { value: '', label: 'Select subcategory...' },
      { value: 'employment_income', label: 'Employment Income' },
      { value: 'business_income', label: 'Business Income' },
      { value: 'investment_income', label: 'Investment Income' },
      { value: 'rental_income', label: 'Rental Income' },
      { value: 'passive_income', label: 'Passive Income' },
      { value: 'other_income', label: 'Other Income' },
    ],
    [EntryCategory.EXPENSES]: [
      { value: '', label: 'Select subcategory...' },
      { value: 'housing', label: 'Housing' },
      { value: 'utilities', label: 'Utilities' },
      { value: 'transportation', label: 'Transportation' },
      { value: 'food', label: 'Food & Dining' },
      { value: 'healthcare', label: 'Healthcare' },
      { value: 'personal', label: 'Personal' },
    ],
  };
  return options[category] || [];
};

const SmartEntryModal: React.FC<SmartEntryModalProps> = ({
  isOpen,
  onClose,
  category,
  subcategory,
  onSuccess,
  editingEntry
}) => {
  const [formData, setFormData] = useState<FinancialEntryCreate>({
    category: category || EntryCategory.ASSETS,
    subcategory: subcategory || '',
    description: '',
    amount: 0,
    currency: 'USD',
    frequency: FrequencyType.ONE_TIME,
    notes: '',
    // Asset allocation fields
    real_estate_percentage: undefined,
    stocks_percentage: undefined,
    bonds_percentage: undefined,
    cash_percentage: undefined,
    alternative_percentage: undefined
  });

  const createMutation = useCreateFinancialEntryMutation();
  const createProfileMutation = useCreateProfileEntryMutation();

  // Update form data when modal opens or category changes
  useEffect(() => {
    if (isOpen) {
      setFormData(prev => ({
        ...prev,
        category: category || EntryCategory.ASSETS,
        subcategory: subcategory || ''
      }));
    }
  }, [isOpen, category, subcategory]);

  // Initialize form with editing entry data if provided
  useEffect(() => {
    if (isOpen && editingEntry) {
      console.log('📝 Initializing form with editing entry:', editingEntry);
      
      // Check if this is a profile entry
      if (typeof editingEntry.id === 'string' && editingEntry.id.startsWith('profile-')) {
        setFormData(prev => ({
          ...prev,
          category: EntryCategory.PROFILE,
          subcategory: 'Personal Information',
          description: editingEntry.description,
          amount: 0, // Profile entries always have amount 0
          notes: editingEntry.notes,
          frequency: FrequencyType.ONE_TIME
        }));
      } else {
        // Regular financial entry
        setFormData(prev => ({
          ...prev,
          category: editingEntry.category || category || EntryCategory.ASSETS,
          subcategory: editingEntry.subcategory || subcategory || '',
          description: editingEntry.description || '',
          amount: editingEntry.amount || 0,
          notes: editingEntry.notes || '',
          frequency: editingEntry.frequency || FrequencyType.ONE_TIME
        }));
      }
    }
  }, [isOpen, editingEntry, category, subcategory]);

  // Debug logging for formData changes
  useEffect(() => {
    console.log('📝 FormData updated:', {
      category: formData.category,
      subcategory: formData.subcategory,
      isLiabilities: formData.category === EntryCategory.LIABILITIES,
      isEnhancedType: ['mortgage_real_estate', 'credit_cards', 'auto_loans', 'student_loans', 'personal_loans'].includes(formData.subcategory)
    });
  }, [formData.category, formData.subcategory]);

  useEffect(() => {
    if (category) {
      setFormData(prev => ({ ...prev, category }));
    }
    if (subcategory) {
      setFormData(prev => ({ ...prev, subcategory }));
    }
  }, [category, subcategory]);

  const handleSuggestionClick = (suggestion: any) => {
    setFormData({
      ...formData,
      description: suggestion.name,
      amount: suggestion.avgValue,
      frequency: suggestion.frequency || FrequencyType.ONE_TIME,
      notes: suggestion.description,
      // Set allocation percentages from suggestion (smart defaults)
      real_estate_percentage: suggestion.real_estate_percentage || 0,
      stocks_percentage: suggestion.stocks_percentage || 0,
      bonds_percentage: suggestion.bonds_percentage || 0,
      cash_percentage: suggestion.cash_percentage || 0,
      alternative_percentage: suggestion.alternative_percentage || 0
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // For profile/benefits/tax categories, we don't require amount > 0
    const isProfileCategory = formData.category === EntryCategory.PROFILE || 
                              formData.category === EntryCategory.BENEFITS || 
                              formData.category === EntryCategory.TAX_INFO;
    
    if (!formData.description || (!isProfileCategory && formData.amount <= 0)) {
      alert('Please fill in all required fields');
      return;
    }

    // Ensure amount is a proper number
    const submissionData = {
      ...formData,
      amount: parseFloat(formData.amount.toString()),
      // Set frequency to ONE_TIME for profile categories
      frequency: isProfileCategory ? FrequencyType.ONE_TIME : formData.frequency
    };

    try {
      console.log('📤 Submitting entry:', submissionData);
      console.log('📤 Subcategory value being sent:', submissionData.subcategory);
      console.log('📤 Full form data:', JSON.stringify(submissionData, null, 2));
      
      let result;
      if (isProfileCategory) {
        // Check if we're editing an existing profile entry
        if (editingEntry && typeof editingEntry.id === 'string' && editingEntry.id.startsWith('profile-')) {
          console.log('🔄 Updating existing profile entry:', editingEntry.id);
          console.log('🔍 SMART MODAL DEBUG - Edit path taken for profile entry');
          
          // Import profile API for direct update
          const { profileApi } = await import('../../utils/profile-api');
          
          // Map the form data to the appropriate profile field
          let updateData: any = {};
          
          switch (editingEntry.id) {
            case 'profile-age':
              updateData.age = parseInt(submissionData.notes) || null;
              break;
            case 'profile-state':
              updateData.state = submissionData.notes || null;
              break;
            case 'profile-notes':
              updateData.notes = `Name: ${submissionData.notes}`;
              break;
            case 'profile-marital':
              updateData.marital_status = submissionData.notes || null;
              break;
            case 'profile-employment':
              updateData.employment_status = submissionData.notes || null;
              break;
            case 'profile-occupation':
              updateData.occupation = submissionData.notes || null;
              break;
            case 'profile-gender':
              updateData.gender = submissionData.notes || null;
              break;
            case 'profile-phone':
              updateData.phone = submissionData.notes || null;
              break;
            case 'profile-city':
              updateData.city = submissionData.notes || null;
              break;
            case 'profile-risk':
              updateData.risk_tolerance = submissionData.notes || null;
              break;
            default:
              console.warn('Unknown profile field for update:', editingEntry.id);
              updateData.notes = `${submissionData.description}: ${submissionData.notes}`;
          }
          
          console.log('📤 Profile update data:', updateData);
          result = await profileApi.updateProfile(updateData);
          console.log('✅ Profile entry updated successfully:', result);
        } else {
          // Creating new profile entry
          console.log('🔍 SMART MODAL DEBUG - Create path taken for new profile entry');
          console.log('📤 Submission data being sent to createProfileMutation:', submissionData);
          result = await createProfileMutation.mutateAsync(submissionData);
          console.log('✅ Profile entry created successfully:', result);
        }
      } else {
        // Use financial API for financial categories
        result = await createMutation.mutateAsync(submissionData);
        console.log('✅ Financial entry created successfully:', result);
      }
      
      onSuccess?.();
      onClose();
      
      // Reset form
      setFormData({
        category: category || EntryCategory.ASSETS,
        subcategory: subcategory || '',
        description: '',
        amount: 0,
        currency: 'USD',
        frequency: FrequencyType.ONE_TIME,
        notes: '',
        // Asset allocation fields
        real_estate_percentage: undefined,
        stocks_percentage: undefined,
        bonds_percentage: undefined,
        cash_percentage: undefined,
        alternative_percentage: undefined
      });
    } catch (error: any) {
      console.error('❌ Failed to create entry:', error);
      console.error('❌ Error details:', {
        status_code: error?.status_code,
        detail: error?.detail,
        message: error?.message,
        fullError: error
      });
      
      // More detailed error message
      let errorMessage = 'Failed to save entry: ';
      if (error?.status_code === 401) {
        errorMessage += 'Your session has expired. Please refresh the page and log in again.';
        // Don't auto-redirect, let user decide
        setTimeout(() => {
          if (confirm('Your session has expired. Would you like to refresh the page to log in again?')) {
            window.location.reload();
          }
        }, 100);
      } else if (error?.status_code === 422) {
        errorMessage += `Invalid data. ${error?.detail || 'Please check your inputs.'}`;
      } else if (error?.detail) {
        errorMessage += error.detail;
      } else if (error instanceof Error) {
        errorMessage += error.message;
      } else {
        errorMessage += 'Unknown error';
      }
      
      alert(errorMessage);
    }
  };

  if (!isOpen) return null;

  const categoryName = formData.subcategory || 'General';
  const suggestions = SMART_SUGGESTIONS[formData.category]?.[categoryName] || [];

  const categoryOptions = [
    { value: EntryCategory.PROFILE, label: 'Profile' },
    { value: EntryCategory.ASSETS, label: 'Assets' },
    { value: EntryCategory.LIABILITIES, label: 'Liabilities' },
    { value: EntryCategory.INCOME, label: 'Income' },
    { value: EntryCategory.EXPENSES, label: 'Expenses' },
    { value: EntryCategory.BENEFITS, label: 'Benefits' },
    { value: EntryCategory.TAX_INFO, label: 'Tax Info' },
  ];

  const frequencyOptions = [
    { value: FrequencyType.ONE_TIME, label: 'One-time' },
    { value: FrequencyType.MONTHLY, label: 'Monthly' },
    { value: FrequencyType.ANNUALLY, label: 'Annually' },
    { value: FrequencyType.QUARTERLY, label: 'Quarterly' },
    { value: FrequencyType.WEEKLY, label: 'Weekly' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2">
      <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 sm:p-6 rounded-t-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white">
                Add {formData.category.charAt(0).toUpperCase() + formData.category.slice(1)} Entry
              </h2>
              {formData.subcategory && (
                <p className="text-blue-100 text-sm mt-1">
                  Subcategory: {getSubcategoryOptions(formData.category).find(opt => opt.value === formData.subcategory)?.label || formData.subcategory}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Smart Suggestions */}
        {suggestions.length > 0 && (
          <div className="p-6 border-b bg-gray-700 border-gray-600">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-300">
                Smart Suggestions for {categoryName}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-left p-3 bg-gray-700 border border-gray-600 rounded-lg hover:border-blue-400 hover:bg-gray-600 transition-colors"
                >
                  <div className="font-medium text-gray-100 text-sm">{suggestion.name}</div>
                  <div className="text-blue-600 text-sm font-semibold">
                    ${suggestion.avgValue.toLocaleString()}
                  </div>
                  <div className="text-xs text-gray-300">{suggestion.description}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Check if we should show SmartLiabilityForm */}
        {formData.category === EntryCategory.LIABILITIES && 
         formData.subcategory && 
         ['mortgage_real_estate', 'credit_cards', 'auto_loans', 'student_loans', 'personal_loans'].includes(formData.subcategory) ? (
          /* Smart Liability Form */
          <div className="p-6">
            <SmartLiabilityForm
              subcategory={formData.subcategory}
              isEditing={false}
              onSubmit={async (data) => {
                try {
                  console.log('💳 Smart liability form submitted from modal:', data);
                  const result = await createMutation.mutateAsync(data);
                  console.log('✅ Smart form create successful:', result);
                  onSuccess?.();
                  onClose();
                } catch (error: any) {
                  console.error('❌ Smart form submission failed:', error);
                  alert(`❌ Failed to create entry. Error: ${error.message || error.detail || error.toString()}`);
                }
              }}
              onCancel={onClose}
            />
          </div>
        ) : (
          /* Basic Form */
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-1">
                Category
              </label>
              <Select
                options={categoryOptions}
                value={formData.category}
                onChange={(e) => {
                  console.log('🔄 Category changed to:', e.target.value);
                  setFormData({...formData, category: e.target.value as EntryCategory, subcategory: ''});
                }}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-1">
                Subcategory
              </label>
              <Select
                value={formData.subcategory}
                onChange={(e) => {
                  console.log('🔄 Subcategory changed to:', e.target.value);
                  setFormData({...formData, subcategory: e.target.value});
                }}
                options={getSubcategoryOptions(formData.category)}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <Input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Enter a clear description"
              leftIcon={<FileText className="w-4 h-4" />}
              required
            />
          </div>

          {/* Custom fields for Profile/Benefits/Tax categories */}
          {(formData.category === EntryCategory.PROFILE || 
            formData.category === EntryCategory.BENEFITS || 
            formData.category === EntryCategory.TAX_INFO) ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-200 mb-1">
                    Value
                  </label>
                  <Input
                    type="text"
                    value={formData.notes || ''}
                    onChange={(e) => {
                      // For profile categories, store text in notes field, not amount
                      setFormData({
                        ...formData, 
                        notes: e.target.value,
                        amount: 0 // Set amount to 0 for profile entries
                      });
                    }}
                    placeholder={
                      formData.category === EntryCategory.PROFILE ? "e.g., 45, California, Married" :
                      formData.category === EntryCategory.BENEFITS ? "e.g., 3500, Full retirement at 67" :
                      "e.g., 32%, Married filing jointly"
                    }
                  />
                </div>
              </div>

            </>
          ) : (
            /* Regular financial form fields */
            <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-1">
                Amount *
              </label>
              <Input
                type="text"
                inputMode="decimal"
                value={formData.amount > 0 ? formData.amount.toLocaleString('en-US', {
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 2,
                }) : ''}
                onChange={(e) => {
                  let val = e.target.value;
                  
                  // Remove all non-numeric characters except decimal and commas
                  val = val.replace(/[^0-9.,]/g, '');
                  
                  // Remove commas for processing
                  const cleanVal = val.replace(/,/g, '');
                  
                  // If empty, set to 0
                  if (cleanVal === '') {
                    setFormData({...formData, amount: 0});
                    return;
                  }
                  
                  // Remove leading zeros (except for 0.x decimals)
                  let processedVal = cleanVal;
                  if (processedVal.length > 1 && processedVal[0] === '0' && processedVal[1] !== '.') {
                    processedVal = processedVal.replace(/^0+/, '');
                    if (processedVal === '') processedVal = '0';
                  }
                  
                  // Prevent multiple decimals
                  const parts = processedVal.split('.');
                  if (parts.length > 2) {
                    processedVal = parts[0] + '.' + parts.slice(1).join('');
                  }
                  
                  // Limit decimal places to 2
                  if (parts.length === 2 && parts[1].length > 2) {
                    processedVal = parts[0] + '.' + parts[1].substring(0, 2);
                  }
                  
                  const num = parseFloat(processedVal);
                  if (!isNaN(num)) {
                    setFormData({...formData, amount: num});
                  } else {
                    setFormData({...formData, amount: 0});
                  }
                }}
                placeholder="0"
                leftIcon={<DollarSign className="w-4 h-4" />}
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-1">
                Frequency
              </label>
              <Select
                options={frequencyOptions}
                value={formData.frequency}
                onChange={(e) => setFormData({...formData, frequency: e.target.value as FrequencyType})}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({...formData, notes: e.target.value})}
              placeholder="Additional details (optional)"
              className="w-full p-3 border border-gray-600 bg-gray-700 text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={3}
            />
          </div>
            </>
          )}

          {/* Asset Allocation Section */}
          {formData.category === EntryCategory.ASSETS && (
            <div className="border-t border-gray-600 pt-4">
              <h4 className="text-lg font-semibold text-green-300 mb-3 flex items-center">
                <DollarSign className="w-5 h-5 mr-2" />
                Asset Allocation (How is this asset allocated?)
              </h4>
              <p className="text-sm text-green-200 mb-4">
                For accurate portfolio analysis, tell us how this asset is allocated across different asset classes:
              </p>
              
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <Input
                  label="Real Estate %"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.real_estate_percentage || ''}
                  onChange={(e) => setFormData({...formData, real_estate_percentage: e.target.value ? Number(e.target.value) : undefined})}
                  placeholder="0"
                />
                
                <Input
                  label="Stocks %"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.stocks_percentage || ''}
                  onChange={(e) => setFormData({...formData, stocks_percentage: e.target.value ? Number(e.target.value) : undefined})}
                  placeholder="0"
                />
                
                <Input
                  label="Bonds %"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.bonds_percentage || ''}
                  onChange={(e) => setFormData({...formData, bonds_percentage: e.target.value ? Number(e.target.value) : undefined})}
                  placeholder="0"
                />
                
                <Input
                  label="Cash %"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.cash_percentage || ''}
                  onChange={(e) => setFormData({...formData, cash_percentage: e.target.value ? Number(e.target.value) : undefined})}
                  placeholder="0"
                />
                
                <Input
                  label="Alternative %"
                  type="number"
                  min="0"
                  max="100"
                  value={formData.alternative_percentage || ''}
                  onChange={(e) => setFormData({...formData, alternative_percentage: e.target.value ? Number(e.target.value) : undefined})}
                  placeholder="0"
                />
              </div>
              
              {/* Percentage validation */}
              <div className="mt-3">
                <div className="text-xs text-green-200">
                  <strong>Total: {(formData.real_estate_percentage || 0) + (formData.stocks_percentage || 0) + (formData.bonds_percentage || 0) + (formData.cash_percentage || 0) + (formData.alternative_percentage || 0)}%</strong>
                  {((formData.real_estate_percentage || 0) + (formData.stocks_percentage || 0) + (formData.bonds_percentage || 0) + (formData.cash_percentage || 0) + (formData.alternative_percentage || 0)) > 100 && (
                    <span className="text-red-400 ml-2">⚠️ Total exceeds 100%</span>
                  )}
                  {((formData.real_estate_percentage || 0) + (formData.stocks_percentage || 0) + (formData.bonds_percentage || 0) + (formData.cash_percentage || 0) + (formData.alternative_percentage || 0)) === 100 && (
                    <span className="text-green-400 ml-2">✅ Perfect!</span>
                  )}
                </div>
                <div className="text-xs text-gray-400 mt-2">
                  <strong>Examples:</strong>
                  <ul className="mt-1 space-y-1">
                    <li>• Primary Home: Real Estate 100%</li>
                    <li>• 401K: Stocks 60%, Bonds 30%, Real Estate 10%</li>
                    <li>• Bitcoin: Alternative 100%</li>
                    <li>• Checking: Cash 100%</li>
                    <li>• Brokerage: Stocks 70%, Bonds 15%, Cash 10%, Real Estate 5%</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-600">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={createMutation.isLoading || createProfileMutation.isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isLoading || createProfileMutation.isLoading}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            >
              {(createMutation.isLoading || createProfileMutation.isLoading) ? 'Saving...' : 'Save Entry'}
            </Button>
          </div>
        </form>
        )}
      </div>
    </div>
  );
};

export default SmartEntryModal;