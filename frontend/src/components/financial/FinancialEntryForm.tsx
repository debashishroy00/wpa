/**
 * WealthPath AI - Financial Entry Form Component
 */
import React, { useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { DollarSign, Calendar, FileText, Tag } from 'lucide-react';

import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Card from '../ui/Card';
import { EntryCategory, FrequencyType, FinancialEntryCreate, FinancialEntry } from '../../types/financial';
import { useCreateFinancialEntryMutation, useUpdateFinancialEntryMutation } from '../../hooks/use-financial-queries';
import SmartLiabilityForm from './LiabilityForms/SmartLiabilityForm';

// Form validation schema
const financialEntrySchema = z.object({
  category: z.nativeEnum(EntryCategory, {
    required_error: 'Category is required',
  }),
  subcategory: z.string().optional(),
  description: z.string()
    .min(1, 'Description is required')
    .max(255, 'Description must be less than 255 characters'),
  amount: z.number({
      required_error: 'Value is required',
      invalid_type_error: 'Value must be a number'
    })
    .min(0, 'Value must be at least 0')
    .max(999999999.99, 'Value is too large'),
  currency: z.string().default('USD'),
  frequency: z.string()
    .refine((val) => Object.values(FrequencyType).includes(val as FrequencyType), {
      message: 'Invalid frequency value'
    })
    .default(FrequencyType.ONE_TIME),
  entry_date: z.string().optional(),
  notes: z.string().optional(),
  // Asset allocation (new 5-category system)
  real_estate_percentage: z.number().min(0).max(100).optional(),
  stocks_percentage: z.number().min(0).max(100).optional(),
  bonds_percentage: z.number().min(0).max(100).optional(),
  cash_percentage: z.number().min(0).max(100).optional(),
  alternative_percentage: z.number().min(0).max(100).optional(),
  
  // Enhanced liability fields
  interest_rate: z.number().min(0).max(50).optional(),
  loan_term_months: z.number().min(0).max(600).optional(),
  remaining_months: z.number().min(0).max(600).optional(),
  minimum_payment: z.number().min(0).optional(),
  is_fixed_rate: z.boolean().optional(),
  loan_start_date: z.string().optional(),
  original_amount: z.number().min(0).optional(),
  loan_details: z.string().optional(),
});

type FormData = z.infer<typeof financialEntrySchema>;

interface FinancialEntryFormProps {
  entry?: FinancialEntry; // For editing
  onSuccess?: () => void;
  onCancel?: () => void;
}

// Helper function to format currency input with commas
const formatCurrencyInput = (value: number): string => {
  // Format number with commas but no currency symbol for input
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
};

const FinancialEntryForm: React.FC<FinancialEntryFormProps> = ({
  entry,
  onSuccess,
  onCancel,
}) => {
  const isEditing = !!entry;
  const createMutation = useCreateFinancialEntryMutation();
  const updateMutation = useUpdateFinancialEntryMutation();

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
    watch,
    setValue,
  } = useForm<FormData>({
    resolver: zodResolver(financialEntrySchema),
    defaultValues: {
      category: EntryCategory.ASSETS,
      subcategory: '',
      description: '',
      amount: 0,
      currency: 'USD',
      frequency: FrequencyType.ONE_TIME,
      entry_date: '',
      notes: '',
      real_estate_percentage: undefined,
      stocks_percentage: undefined,
      bonds_percentage: undefined,
      cash_percentage: undefined,
      alternative_percentage: undefined,
      // Enhanced liability fields
      interest_rate: undefined,
      loan_term_months: undefined,
      remaining_months: undefined,
      minimum_payment: undefined,
      is_fixed_rate: undefined,
      loan_start_date: undefined,
      original_amount: undefined,
      loan_details: undefined,
    },
  });

  // Reset form when entry prop changes (for editing)
  useEffect(() => {
    if (entry) {
      console.log('🔍 Setting form data for entry:', entry);
      console.log('🔍 Entry object keys:', Object.keys(entry));
      console.log('🔍 Entry values:', {
        id: entry.id,
        category: entry.category,
        subcategory: entry.subcategory,
        description: entry.description,
        amount: entry.amount,
        frequency: entry.frequency,
        currency: entry.currency,
        entry_date: entry.entry_date,
        interest_rate: entry.interest_rate
      });

      // Ensure frequency is valid, fallback to one-time if not
      let validFrequency = entry.frequency;
      const validFrequencies = Object.values(FrequencyType);
      if (!validFrequencies.includes(entry.frequency)) {
        console.warn('⚠️ Invalid frequency value:', entry.frequency, 'using one-time as fallback');
        validFrequency = FrequencyType.ONE_TIME;
      }

      const formData = {
        category: entry.category,
        subcategory: entry.subcategory || '',
        description: entry.description || '',
        amount: Number(entry.amount) || 0,
        currency: entry.currency || 'USD',
        frequency: validFrequency,
        entry_date: entry.entry_date ? new Date(entry.entry_date).toISOString().split('T')[0] : '',
        notes: entry.notes || '',
        real_estate_percentage: entry.real_estate_percentage || undefined,
        stocks_percentage: entry.stocks_percentage || undefined,
        bonds_percentage: entry.bonds_percentage || undefined,
        cash_percentage: entry.cash_percentage || undefined,
        alternative_percentage: entry.alternative_percentage || undefined,
        // Enhanced liability fields
        interest_rate: entry.interest_rate || undefined,
        loan_term_months: entry.loan_term_months || undefined,
        remaining_months: entry.remaining_months || undefined,
        minimum_payment: entry.minimum_payment || undefined,
        is_fixed_rate: entry.is_fixed_rate || undefined,
        loan_start_date: entry.loan_start_date ? new Date(entry.loan_start_date).toISOString().split('T')[0] : undefined,
        original_amount: entry.original_amount || undefined,
        loan_details: entry.loan_details || undefined,
      };
      console.log('📝 Form data being set:', formData);
      
      // Use both reset and setValue for maximum compatibility
      reset(formData);
      
      // Also set individual values as backup
      Object.entries(formData).forEach(([key, value]) => {
        setValue(key as keyof FormData, value);
      });
      
    } else {
      console.log('🆕 No entry provided, using defaults for new entry');
      // Reset to defaults for new entry
      reset({
        category: EntryCategory.ASSETS,
        subcategory: '',
        description: '',
        amount: 0,
        currency: 'USD',
        frequency: FrequencyType.ONE_TIME,
        entry_date: '',
        notes: '',
        real_estate_percentage: undefined,
        stocks_percentage: undefined,
        bonds_percentage: undefined,
        cash_percentage: undefined,
        alternative_percentage: undefined,
        // Enhanced liability fields
        interest_rate: undefined,
        loan_term_months: undefined,
        remaining_months: undefined,
        minimum_payment: undefined,
        is_fixed_rate: undefined,
        loan_start_date: undefined,
        original_amount: undefined,
        loan_details: undefined,
      });
    }
  }, [entry, reset, setValue]);

  const selectedCategory = watch('category');
  const selectedSubcategory = watch('subcategory');
  const allFormValues = watch(); // Watch all form values for debugging

  // Subcategory options based on category
  const getSubcategoryOptions = (category: EntryCategory) => {
    const options = {
      [EntryCategory.ASSETS]: [
        { value: 'real_estate', label: 'Real Estate' },
        { value: 'retirement_accounts', label: 'Retirement Accounts' },
        { value: 'investment_accounts', label: 'Investment Accounts' },
        { value: 'cash_bank_accounts', label: 'Cash & Bank Accounts' },
        { value: 'personal_property', label: 'Personal Property' },
        { value: 'business_assets', label: 'Business Assets' },
        { value: 'other_assets', label: 'Other Assets' },
      ],
      [EntryCategory.LIABILITIES]: [
        { value: 'mortgage_real_estate', label: 'Mortgage & Real Estate' },
        { value: 'credit_cards', label: 'Credit Cards' },
        { value: 'auto_loans', label: 'Auto Loans' },
        { value: 'student_loans', label: 'Student Loans' },
        { value: 'personal_loans', label: 'Personal Loans' },
        { value: 'other_debt', label: 'Other Debt' },
      ],
      [EntryCategory.INCOME]: [
        { value: 'employment_income', label: 'Employment Income' },
        { value: 'business_income', label: 'Business Income' },
        { value: 'investment_income', label: 'Investment Income' },
        { value: 'rental_income', label: 'Rental Income' },
        { value: 'passive_income', label: 'Passive Income' },
        { value: 'other_income', label: 'Other Income' },
      ],
      [EntryCategory.EXPENSES]: [
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

  const categoryOptions = [
    { value: EntryCategory.ASSETS, label: 'Assets' },
    { value: EntryCategory.LIABILITIES, label: 'Liabilities' },
    { value: EntryCategory.INCOME, label: 'Income' },
    { value: EntryCategory.EXPENSES, label: 'Expenses' },
  ];

  const frequencyOptions = [
    { value: FrequencyType.ONE_TIME, label: 'One-time' },
    { value: FrequencyType.MONTHLY, label: 'Monthly' },
    { value: FrequencyType.QUARTERLY, label: 'Quarterly' },
    { value: FrequencyType.ANNUALLY, label: 'Annually' },
    { value: FrequencyType.WEEKLY, label: 'Weekly' },
    { value: FrequencyType.DAILY, label: 'Daily' },
  ];

  const onSubmit = async (data: FormData) => {
    console.log('🚀 Form submission started');
    console.log('📝 Form data:', data);
    console.log('✏️ Is editing:', isEditing);
    console.log('📄 Entry:', entry);
    
    try {
      if (isEditing && entry) {
        console.log('🔄 Updating entry with ID:', entry.id);
        const updateData = {
          id: parseInt(entry.id),
          update: {
            description: data.description,
            amount: data.amount,
            frequency: (data.category === EntryCategory.PROFILE || 
                      data.category === EntryCategory.BENEFITS || 
                      data.category === EntryCategory.TAX_INFO) 
                     ? FrequencyType.ONE_TIME 
                     : data.frequency as FrequencyType,
            subcategory: data.subcategory,
            notes: data.notes,
            real_estate_percentage: data.real_estate_percentage,
            stocks_percentage: data.stocks_percentage,
            bonds_percentage: data.bonds_percentage,
            cash_percentage: data.cash_percentage,
            alternative_percentage: data.alternative_percentage,
            // Enhanced liability fields
            interest_rate: data.interest_rate,
            loan_term_months: data.loan_term_months,
            remaining_months: data.remaining_months,
            minimum_payment: data.minimum_payment,
            is_fixed_rate: data.is_fixed_rate,
            loan_start_date: data.loan_start_date,
            original_amount: data.original_amount,
            loan_details: data.loan_details,
          },
        };
        console.log('📤 Update data being sent:', updateData);
        
        const result = await updateMutation.mutateAsync(updateData);
        console.log('✅ Update successful:', result);
      } else {
        console.log('➕ Creating new entry');
        const entryData: FinancialEntryCreate = {
          category: data.category,
          subcategory: data.subcategory,
          description: data.description,
          amount: data.amount,
          currency: data.currency,
          frequency: (data.category === EntryCategory.PROFILE || 
                     data.category === EntryCategory.BENEFITS || 
                     data.category === EntryCategory.TAX_INFO) 
                    ? FrequencyType.ONE_TIME 
                    : data.frequency as FrequencyType,
          entry_date: data.entry_date || undefined,
          notes: data.notes,
          real_estate_percentage: data.real_estate_percentage,
          stocks_percentage: data.stocks_percentage,
          bonds_percentage: data.bonds_percentage,
          cash_percentage: data.cash_percentage,
          alternative_percentage: data.alternative_percentage,
          // Enhanced liability fields
          interest_rate: data.interest_rate,
          loan_term_months: data.loan_term_months,
          remaining_months: data.remaining_months,
          minimum_payment: data.minimum_payment,
          is_fixed_rate: data.is_fixed_rate,
          loan_start_date: data.loan_start_date,
          original_amount: data.original_amount,
          loan_details: data.loan_details,
        };
        console.log('📤 Create data being sent:', entryData);
        
        const result = await createMutation.mutateAsync(entryData);
        console.log('✅ Create successful:', result);
      }
      
      console.log('🎉 Entry saved successfully');
      alert(`✅ Entry ${isEditing ? 'updated' : 'created'} successfully!`);
      
      // Call onSuccess with a small delay to allow user to see success message
      setTimeout(() => {
        onSuccess?.();
      }, 100);
      
      if (!isEditing) {
        reset();
      }
    } catch (error) {
      console.error('❌ Failed to save financial entry:', error);
      const errorMessage = error.message || error.detail || error.toString();
      
      if (errorMessage.includes('Authentication expired') || errorMessage.includes('Could not validate credentials')) {
        alert('🔐 Your session has expired. Please refresh the page to continue.');
        window.location.reload();
      } else {
        alert(`❌ Failed to ${isEditing ? 'update' : 'create'} entry. Please try again. Error: ${errorMessage}`);
      }
      // Don't call onSuccess on error - stay on the form
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  return (
    <Card className="max-w-2xl mx-auto" key={entry?.id || 'new'}>
      <Card.Header>
        <Card.Title>
          {isEditing ? 'Edit Financial Entry' : 'Add Financial Entry'}
        </Card.Title>
        <p className="text-sm text-gray-300 mt-1">
          Enter your financial data to track your net worth and progress
        </p>
      </Card.Header>

      <form onSubmit={handleSubmit(onSubmit, (errors) => {
        console.log('❌ Form validation failed:', errors);
        alert('Form validation failed. Please check the highlighted fields.');
      })} className="space-y-6">
        {/* Debug info - remove in production */}
        {isEditing && (
          <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-3 text-xs">
            <details>
              <summary className="text-blue-300 cursor-pointer mb-2">🔍 Debug Form Values</summary>
              <div className="text-blue-200 space-y-1">
                <div><strong>Entry ID:</strong> {entry?.id}</div>
                <div><strong>Form Values:</strong> {JSON.stringify(allFormValues, null, 2)}</div>
                <div><strong>Errors:</strong> {JSON.stringify(errors, null, 2)}</div>
                <div className="mt-2">
                  <button
                    type="button"
                    onClick={async () => {
                      console.log('🧪 Testing direct mutation...');
                      try {
                        const result = await updateMutation.mutateAsync({
                          id: parseInt(entry.id),
                          update: {
                            description: allFormValues.description || 'Test Update',
                            amount: allFormValues.amount || 1000,
                            frequency: allFormValues.frequency as FrequencyType || FrequencyType.ONE_TIME,
                            subcategory: allFormValues.subcategory,
                            notes: allFormValues.notes,
                          },
                        });
                        console.log('✅ Direct mutation successful:', result);
                        alert('Direct mutation worked!');
                      } catch (error) {
                        console.error('❌ Direct mutation failed:', error);
                        alert('Direct mutation failed: ' + error);
                      }
                    }}
                    className="px-2 py-1 bg-green-600 text-white text-xs rounded"
                  >
                    🧪 Test Direct Update
                  </button>
                </div>
              </div>
            </details>
          </div>
        )}
        
        {/* Category Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Controller
            name="category"
            control={control}
            render={({ field }) => (
              <Select
                label="Category *"
                options={categoryOptions}
                error={errors.category?.message}
                {...field}
              />
            )}
          />

          <Controller
            name="subcategory"
            control={control}
            render={({ field }) => (
              <Select
                label="Subcategory"
                options={[
                  { value: '', label: 'Select subcategory...' },
                  ...getSubcategoryOptions(selectedCategory),
                ]}
                error={errors.subcategory?.message}
                {...field}
              />
            )}
          />
        </div>

        {/* Smart Liability Form - Show when liability subcategory is selected */}
        {selectedCategory === EntryCategory.LIABILITIES && selectedSubcategory && 
         ['mortgage_real_estate', 'credit_cards', 'auto_loans', 'student_loans', 'personal_loans'].includes(selectedSubcategory) && (
          <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-yellow-300">Enhanced Liability Details</h3>
              <span className="text-xs text-yellow-200 bg-yellow-800 px-2 py-1 rounded">
                Smart Form Active
              </span>
            </div>
            <p className="text-sm text-yellow-200 mb-4">
              We'll collect detailed information about this liability to provide better financial advice.
              You can continue with the basic form below if you prefer.
            </p>
            
            <SmartLiabilityForm
              subcategory={selectedSubcategory}
              entry={isEditing ? entry : undefined}
              isEditing={isEditing}
              onSubmit={async (data) => {
                console.log('💳 Smart liability form submitted:', data);
                try {
                  if (isEditing && entry) {
                    // Update existing entry - filter out undefined values
                    const updatePayload: any = {
                      description: data.description,
                      amount: data.amount,
                      frequency: data.frequency || FrequencyType.ONE_TIME,
                      subcategory: data.subcategory,
                    };
                    
                    // Only include optional fields if they have values
                    if (data.notes !== undefined) updatePayload.notes = data.notes;
                    if (data.interest_rate !== undefined) updatePayload.interest_rate = data.interest_rate;
                    if (data.loan_term_months !== undefined) updatePayload.loan_term_months = data.loan_term_months;
                    if (data.remaining_months !== undefined) updatePayload.remaining_months = data.remaining_months;
                    if (data.minimum_payment !== undefined) updatePayload.minimum_payment = data.minimum_payment;
                    if (data.is_fixed_rate !== undefined) updatePayload.is_fixed_rate = data.is_fixed_rate;
                    if (data.loan_start_date !== undefined && data.loan_start_date !== '') updatePayload.loan_start_date = data.loan_start_date;
                    if (data.original_amount !== undefined) updatePayload.original_amount = data.original_amount;
                    if (data.loan_details !== undefined) updatePayload.loan_details = data.loan_details;
                    
                    const updateData = {
                      id: parseInt(entry.id),
                      update: updatePayload,
                    };
                    
                    console.log('📤 Sending update data:', JSON.stringify(updateData, null, 2));
                    const result = await updateMutation.mutateAsync(updateData);
                    console.log('✅ Smart form update successful:', result);
                  } else {
                    // Create new entry
                    const result = await createMutation.mutateAsync(data);
                    console.log('✅ Smart form create successful:', result);
                  }
                  
                  // Call onSuccess immediately
                  onSuccess?.();
                  
                  if (!isEditing) {
                    reset();
                  }
                } catch (error: any) {
                  console.error('❌ Smart form submission failed:', error);
                  
                  // Extract error details
                  let errorMessage = '';
                  if (error.response?.data?.detail) {
                    // Backend validation error
                    if (Array.isArray(error.response.data.detail)) {
                      errorMessage = error.response.data.detail.map((e: any) => `${e.loc?.join('.')}: ${e.msg}`).join(', ');
                    } else {
                      errorMessage = error.response.data.detail;
                    }
                  } else {
                    errorMessage = error.message || error.detail || error.toString();
                  }
                  
                  if (errorMessage.includes('Authentication expired') || errorMessage.includes('Could not validate credentials')) {
                    alert('🔐 Your session has expired. Please refresh the page to continue.');
                    window.location.reload();
                  } else {
                    alert(`❌ Failed to ${isEditing ? 'update' : 'create'} liability.\n\nError: ${errorMessage}`);
                  }
                  // Don't call onSuccess on error - stay on the form
                }
              }}
              onCancel={() => {
                if (isEditing) {
                  onCancel?.();
                } else {
                  // Reset subcategory to show basic form
                  setValue('subcategory', '');
                }
              }}
            />
            
            <div className="mt-4 pt-4 border-t border-yellow-600">
              <p className="text-xs text-yellow-200">
                Or continue with the basic form below for simple entry...
              </p>
            </div>
          </div>
        )}

        {/* Custom Forms for Profile/Benefits/Tax Info */}
        {(selectedCategory === EntryCategory.PROFILE || 
          selectedCategory === EntryCategory.BENEFITS || 
          selectedCategory === EntryCategory.TAX_INFO) && (
          <>
            {/* Profile/Benefits/Tax Custom Fields */}
            <Input
              label="Description *"
              placeholder={
                selectedCategory === EntryCategory.PROFILE ? "e.g., Age: 45, State: California, Marital Status: Married" :
                selectedCategory === EntryCategory.BENEFITS ? "e.g., Social Security: $3,500/month at 67" :
                "e.g., Filing Status: Married Filing Jointly, Tax Bracket: 32%"
              }
              leftIcon={<FileText className="w-4 h-4" />}
              error={errors.description?.message}
              {...register('description')}
            />

            {/* Value field instead of Amount for these categories */}
            <Input
              label="Value"
              placeholder={
                selectedCategory === EntryCategory.PROFILE ? "45" :
                selectedCategory === EntryCategory.BENEFITS ? "3500" :
                "32"
              }
              leftIcon={<Tag className="w-4 h-4" />}
              type="text"
              {...register('amount', { 
                setValueAs: (value) => selectedCategory === EntryCategory.PROFILE ? parseFloat(value) || 0 : parseFloat(value) || 0 
              })}
            />

            {/* Custom Notes for context */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Additional Details
              </label>
              <textarea
                placeholder={
                  selectedCategory === EntryCategory.PROFILE ? "Additional personal information..." :
                  selectedCategory === EntryCategory.BENEFITS ? "Benefit calculation details..." :
                  "Tax planning notes..."
                }
                className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                {...register('notes')}
              />
            </div>
          </>
        )}

        {/* Basic Financial Form - Hide when Smart Liability Form or Custom Forms are active */}
        {!(selectedCategory === EntryCategory.LIABILITIES && selectedSubcategory && 
         ['mortgage_real_estate', 'credit_cards', 'auto_loans', 'student_loans', 'personal_loans'].includes(selectedSubcategory)) &&
        !(selectedCategory === EntryCategory.PROFILE || 
          selectedCategory === EntryCategory.BENEFITS || 
          selectedCategory === EntryCategory.TAX_INFO) && (
        <>
        {/* Description */}
        <Input
          label="Description *"
          placeholder="e.g., Chase Checking Account, Monthly Rent, etc."
          leftIcon={<FileText className="w-4 h-4" />}
          error={errors.description?.message}
          {...register('description')}
        />

        {/* Amount and Currency */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <Controller
              name="amount"
              control={control}
              render={({ field }) => {
                const [displayValue, setDisplayValue] = React.useState(
                  field.value && field.value > 0 ? formatCurrencyInput(field.value) : ''
                );
                
                // Update displayValue when field.value changes (e.g., when editing an entry)
                React.useEffect(() => {
                  if (field.value && field.value > 0) {
                    setDisplayValue(formatCurrencyInput(field.value));
                  } else {
                    setDisplayValue('');
                  }
                }, [field.value]);
                
                return (
                  <Input
                    label="Amount *"
                    type="text"
                    inputMode="decimal"
                    placeholder="0"
                    leftIcon={<DollarSign className="w-4 h-4" />}
                    error={errors.amount?.message}
                    value={displayValue}
                    onChange={(e) => {
                      let val = e.target.value;
                      
                      // Remove all non-numeric characters except decimal and commas
                      val = val.replace(/[^0-9.,]/g, '');
                      
                      // Remove commas for processing
                      const cleanVal = val.replace(/,/g, '');
                      
                      // If empty, set to empty string
                      if (cleanVal === '') {
                        setDisplayValue('');
                        field.onChange(0);
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
                      
                      // Format with commas while typing
                      const num = parseFloat(processedVal);
                      if (!isNaN(num)) {
                        const formatted = formatCurrencyInput(num);
                        setDisplayValue(formatted);
                        field.onChange(num);
                      } else {
                        setDisplayValue(processedVal);
                        field.onChange(0);
                      }
                    }}
                  />
                );
              }}
            />
          </div>

          <Input
            label="Currency"
            value="USD"
            disabled
            {...register('currency')}
          />
        </div>

        {/* Interest Rate - Only for Cash & Bank Accounts and Investment Accounts */}
        {(selectedCategory === EntryCategory.ASSETS && 
          (selectedSubcategory === 'cash_bank_accounts' || selectedSubcategory === 'investment_accounts')) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Interest Rate / APY (%)"
              type="number"
              step="0.01"
              min="0"
              max="20"
              placeholder="e.g., 4.25"
              leftIcon={<span className="text-green-400 text-sm font-medium">%</span>}
              error={errors.interest_rate?.message}
              {...register('interest_rate', { 
                setValueAs: (value) => value === '' ? undefined : parseFloat(value) 
              })}
            />
            <div className="flex items-end">
              <p className="text-xs text-gray-400 pb-2">
                Enter the current annual percentage yield (APY) for this account. 
                This helps optimize your cash allocation recommendations.
              </p>
            </div>
          </div>
        )}

        {/* Frequency and Date - Only for financial entries */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Controller
            name="frequency"
            control={control}
            render={({ field }) => (
              <Select
                label="Frequency"
                options={frequencyOptions}
                error={errors.frequency?.message}
                {...field}
              />
            )}
          />

          <Input
            label="Entry Date"
            type="date"
            leftIcon={<Calendar className="w-4 h-4" />}
            error={errors.entry_date?.message}
            {...register('entry_date')}
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-200 mb-1">
            Notes
          </label>
          <textarea
            rows={3}
            placeholder="Additional notes or context..."
            className="block w-full rounded-md border-gray-600 bg-gray-700 text-white placeholder:text-gray-400 shadow-sm focus:border-blue-400 focus:ring-blue-400 focus:ring-1"
            {...register('notes')}
          />
          {errors.notes && (
            <p className="mt-1 text-xs text-red-400">{errors.notes.message}</p>
          )}
        </div>

        {/* Asset Allocation - SIMPLIFIED: Show for ALL asset entries */}
        {selectedCategory === EntryCategory.ASSETS && (
          <div className="bg-green-900/20 border border-green-600 rounded-lg p-4">
            <h4 className="text-lg font-medium text-green-300 mb-3 flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              Asset Allocation (How is this asset allocated?)
            </h4>
            <p className="text-sm text-green-200 mb-4">
              For accurate portfolio analysis, tell us how this asset is allocated across different asset classes:
            </p>
            
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <Controller
                name="real_estate_percentage"
                control={control}
                render={({ field }) => (
                  <Input
                    label="Real Estate %"
                    type="number"
                    min="0"
                    max="100"
                    placeholder="0"
                    error={errors.real_estate_percentage?.message}
                    {...field}
                    value={field.value || ''}
                    onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                  />
                )}
              />
              
              <Controller
                name="stocks_percentage"
                control={control}
                render={({ field }) => (
                  <Input
                    label="Stocks %"
                    type="number"
                    min="0"
                    max="100"
                    placeholder="0"
                    error={errors.stocks_percentage?.message}
                    {...field}
                    value={field.value || ''}
                    onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                  />
                )}
              />
              
              <Controller
                name="bonds_percentage"
                control={control}
                render={({ field }) => (
                  <Input
                    label="Bonds %"
                    type="number"
                    min="0"
                    max="100"
                    placeholder="0"
                    error={errors.bonds_percentage?.message}
                    {...field}
                    value={field.value || ''}
                    onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                  />
                )}
              />
              
              <Controller
                name="cash_percentage"
                control={control}
                render={({ field }) => (
                  <Input
                    label="Cash %"
                    type="number"
                    min="0"
                    max="100"
                    placeholder="0"
                    error={errors.cash_percentage?.message}
                    {...field}
                    value={field.value || ''}
                    onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                  />
                )}
              />
              
              <Controller
                name="alternative_percentage"
                control={control}
                render={({ field }) => (
                  <Input
                    label="Alternative %"
                    type="number"
                    min="0"
                    max="100"
                    placeholder="0"
                    error={errors.alternative_percentage?.message}
                    {...field}
                    value={field.value || ''}
                    onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : undefined)}
                  />
                )}
              />
            </div>
            
            {/* Percentage validation */}
            <div className="mt-3">
              <div className="text-xs text-green-200">
                <strong>Total: {(allFormValues.real_estate_percentage || 0) + (allFormValues.stocks_percentage || 0) + (allFormValues.bonds_percentage || 0) + (allFormValues.cash_percentage || 0) + (allFormValues.alternative_percentage || 0)}%</strong>
                {((allFormValues.real_estate_percentage || 0) + (allFormValues.stocks_percentage || 0) + (allFormValues.bonds_percentage || 0) + (allFormValues.cash_percentage || 0) + (allFormValues.alternative_percentage || 0)) > 100 && (
                  <span className="text-red-400 ml-2">⚠️ Total exceeds 100%</span>
                )}
                {((allFormValues.real_estate_percentage || 0) + (allFormValues.stocks_percentage || 0) + (allFormValues.bonds_percentage || 0) + (allFormValues.cash_percentage || 0) + (allFormValues.alternative_percentage || 0)) === 100 && (
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
        <div className="flex gap-3 pt-6">
          <Button
            type="submit"
            isLoading={isLoading}
            className="flex-1 md:flex-none"
            onClick={(e) => {
              console.log('🖱️ Button clicked!', e);
              // Don't preventDefault - let form submission happen
            }}
          >
            {isEditing ? 'Update Entry' : 'Add Entry'}
          </Button>
          
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isLoading}
            >
              Cancel
            </Button>
          )}
        </div>
        </>
        )}
      </form>
    </Card>
  );
};

export default FinancialEntryForm;