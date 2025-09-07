/**
 * Smart Liability Form - Shows different fields based on liability subcategory
 */
import React, { useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Calculator, DollarSign, Calendar, Info, CheckCircle } from 'lucide-react';

import Button from '../../ui/Button';
import Input from '../../ui/Input';
import Select from '../../ui/Select';
import Card from '../../ui/Card';
import { EntryCategory, FrequencyType, FinancialEntryCreate } from '../../../types/financial';

// Validation schemas for different liability types
const mortgageSchema = z.object({
  description: z.string().min(1, 'Description is required'),
  current_balance: z.number().min(0.01, 'Balance must be positive'),
  monthly_payment: z.number().min(0, 'Monthly payment cannot be negative'),
  interest_rate: z.number().min(0).max(50, 'Interest rate must be between 0% and 50%'),
  loan_term_years: z.number().min(1).max(50, 'Loan term must be between 1 and 50 years'),
  remaining_years: z.number().min(0).max(50, 'Remaining years cannot exceed 50'),
  is_fixed_rate: z.union([z.boolean(), z.string()]).transform((val) => val === true || val === 'true').default(true),
  property_value: z.number().min(0).optional(),
  purchase_date: z.string().optional(),
  escrow_included: z.union([z.boolean(), z.string()]).transform((val) => val === true || val === 'true').optional(),
  tax_deductible: z.union([z.boolean(), z.string()]).transform((val) => val === true || val === 'true').optional(),
  refinance_date: z.string().optional(),
});

const creditCardSchema = z.object({
  card_name: z.string().min(1, 'Card name is required'),
  current_balance: z.number().min(0, 'Balance cannot be negative'),
  credit_limit: z.number().min(1, 'Credit limit must be positive'),
  apr: z.number().min(0).max(50, 'APR must be between 0% and 50%'),
  intro_apr: z.number().min(0).max(50).optional(),
  intro_apr_end_date: z.string().optional(),
  minimum_payment: z.number().min(0).optional(),
  average_monthly_payment: z.number().min(0).optional(),
  rewards_type: z.string().optional(),
});

const autoLoanSchema = z.object({
  vehicle_description: z.string().min(1, 'Vehicle description is required'),
  current_balance: z.number().min(0.01, 'Balance must be positive'),
  monthly_payment: z.number().min(0, 'Monthly payment cannot be negative'),
  interest_rate: z.number().min(0).max(30, 'Interest rate must be between 0% and 30%'),
  original_loan_amount: z.number().min(1, 'Original loan amount must be positive'),
  loan_term_months: z.number().min(1).max(120, 'Loan term must be between 1 and 120 months'),
  remaining_months: z.number().min(0).max(120, 'Remaining months cannot exceed 120'),
  vehicle_value: z.number().min(0).optional(),
  vehicle_year: z.number().min(1900).max(new Date().getFullYear() + 2).optional(),
  vehicle_make: z.string().optional(),
  vehicle_model: z.string().optional(),
});

const studentLoanSchema = z.object({
  loan_servicer: z.string().min(1, 'Loan servicer is required'),
  current_balance: z.number().min(0.01, 'Balance must be positive'),
  monthly_payment: z.number().min(0, 'Monthly payment cannot be negative'),
  interest_rate: z.number().min(0).max(20, 'Interest rate must be between 0% and 20%'),
  loan_type: z.enum(['federal', 'private'], { required_error: 'Loan type is required' }),
  repayment_plan: z.string().optional(),
  subsidized: z.boolean().optional(),
  eligible_for_forgiveness: z.boolean().optional(),
  graduation_date: z.string().optional(),
  first_payment_date: z.string().optional(),
  expected_payoff_date: z.string().optional(),
});

const personalLoanSchema = z.object({
  description: z.string().min(1, 'Description is required'),
  current_balance: z.number().min(0.01, 'Balance must be positive'),
  monthly_payment: z.number().min(0, 'Monthly payment cannot be negative'),
  interest_rate: z.number().min(0).max(50, 'Interest rate must be between 0% and 50%'),
  loan_term_months: z.number().min(1).max(600, 'Loan term must be between 1 and 600 months'),
  remaining_months: z.number().min(0).max(600, 'Remaining months cannot exceed 600'),
  purpose: z.string().optional(),
  secured: z.boolean().default(false),
});

interface SmartLiabilityFormProps {
  subcategory: string;
  entry?: any; // FinancialEntry for editing
  isEditing?: boolean;
  onSubmit: (data: any) => void;
  onCancel?: () => void;
}

// Helper function to calculate monthly payment
const calculateMonthlyPayment = (principal: number, rate: number, months: number): number => {
  if (rate === 0) return principal / months;
  
  const monthlyRate = rate / 100 / 12;
  return principal * (monthlyRate * Math.pow(1 + monthlyRate, months)) / 
         (Math.pow(1 + monthlyRate, months) - 1);
};

// Helper function to calculate payoff time
const calculatePayoffMonths = (balance: number, payment: number, rate: number): number => {
  if (rate === 0) return balance / payment;
  
  const monthlyRate = rate / 100 / 12;
  return Math.log(payment / (payment - balance * monthlyRate)) / 
         Math.log(1 + monthlyRate);
};

const SmartLiabilityForm: React.FC<SmartLiabilityFormProps> = ({ 
  subcategory, 
  entry, 
  isEditing = false, 
  onSubmit, 
  onCancel 
}) => {
  // Determine which schema to use based on subcategory
  const getSchema = () => {
    switch (subcategory) {
      case 'mortgage_real_estate':
        return mortgageSchema;
      case 'credit_cards':
        return creditCardSchema;
      case 'auto_loans':
        return autoLoanSchema;
      case 'student_loans':
        return studentLoanSchema;
      case 'personal_loans':
        return personalLoanSchema;
      default:
        return personalLoanSchema; // Default to personal loan
    }
  };

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState,
    formState: { errors, isSubmitting },
    watch,
    setValue,
    trigger,
  } = useForm({
    resolver: zodResolver(getSchema()),
    defaultValues: getDefaultValues(subcategory, entry, isEditing),
  });

  const allFormValues = watch();

  // Reset form when entry changes (for editing)
  useEffect(() => {
    if (isEditing && entry) {
      const formData = getDefaultValues(subcategory, entry, isEditing);
      reset(formData);
    }
  }, [entry, isEditing, subcategory, reset]);

  function getDefaultValues(subcategory: string, entry?: any, isEditing?: boolean) {
    // If editing, populate with existing entry data
    if (isEditing && entry) {
      console.log('🔍 Loading entry data for editing:', entry);
      const editingData = {
        current_balance: parseFloat(entry.amount) || '',
        monthly_payment: parseFloat(entry.minimum_payment) || '',
        interest_rate: parseFloat(entry.interest_rate) || '',
      };
      console.log('🔍 Basic editing data:', editingData);

      // Safe JSON parsing helper
      const parseDetails = (detailsJson: string) => {
        try {
          return JSON.parse(detailsJson || '{}');
        } catch {
          return {};
        }
      };

      const details = parseDetails(entry.loan_details);

      switch (subcategory) {
        case 'mortgage_real_estate':
          const mortgageDefaults = {
            ...editingData,
            description: entry.description || '',
            loan_term_years: entry.loan_term_months ? Math.round(entry.loan_term_months / 12) : 30,
            remaining_years: entry.remaining_months ? Math.round(entry.remaining_months / 12) : '',
            is_fixed_rate: entry.is_fixed_rate ?? true,
            property_value: details.property_value || '',
            purchase_date: entry.loan_start_date ? 
              new Date(entry.loan_start_date).toISOString().split('T')[0] : '',
            escrow_included: details.escrow_included || false,
            tax_deductible: details.tax_deductible || true,
          };
          console.log('🔍 Mortgage form defaults:', mortgageDefaults);
          return mortgageDefaults;
        case 'credit_cards':
          return {
            ...editingData,
            card_name: entry.description || '',
            credit_limit: details.credit_limit || '',
            apr: entry.interest_rate || '',
            rewards_type: details.rewards_type || '',
          };
        case 'auto_loans':
          return {
            ...editingData,
            vehicle_description: entry.description || '',
            original_loan_amount: entry.original_amount || '',
            loan_term_months: entry.loan_term_months || 60,
            remaining_months: entry.remaining_months || '',
            vehicle_year: details.vehicle_year || new Date().getFullYear(),
            vehicle_make: details.vehicle_make || '',
            vehicle_model: details.vehicle_model || '',
          };
        case 'student_loans':
          return {
            ...editingData,
            loan_servicer: entry.description || '',
            loan_type: details.loan_type || 'federal',
            subsidized: details.subsidized || false,
            eligible_for_forgiveness: details.eligible_for_forgiveness || false,
          };
        default:
          return {
            ...editingData,
            description: entry.description || '',
            loan_term_months: entry.loan_term_months || 36,
            remaining_months: entry.remaining_months || '',
            secured: details.secured || false,
          };
      }
    }

    // Default values for new entries
    const common = {
      current_balance: '',
      monthly_payment: '',
      interest_rate: '',
    };

    switch (subcategory) {
      case 'mortgage_real_estate':
        return {
          ...common,
          description: '',
          loan_term_years: 30,
          remaining_years: '',
          is_fixed_rate: true,
          property_value: '',
          escrow_included: false,
          tax_deductible: true,
        };
      case 'credit_cards':
        return {
          ...common,
          card_name: '',
          credit_limit: '',
          apr: '',
          rewards_type: '',
        };
      case 'auto_loans':
        return {
          ...common,
          vehicle_description: '',
          original_loan_amount: '',
          loan_term_months: 60,
          remaining_months: '',
          vehicle_year: new Date().getFullYear(),
        };
      case 'student_loans':
        return {
          ...common,
          loan_servicer: '',
          loan_type: 'federal',
          subsidized: false,
          eligible_for_forgiveness: false,
        };
      default:
        return {
          ...common,
          description: '',
          loan_term_months: 36,
          remaining_months: '',
          secured: false,
        };
    }
  }

  // Calculate derived values in real-time
  const calculateInsights = () => {
    const balance = parseFloat(allFormValues.current_balance || '0');
    const payment = parseFloat(allFormValues.monthly_payment || '0');
    const rate = parseFloat(allFormValues.interest_rate || '0');

    if (balance <= 0 || payment <= 0) return null;

    const insights = [];
    
    // Calculate payoff time if payment > minimum
    if (payment > 0 && rate >= 0) {
      try {
        const months = calculatePayoffMonths(balance, payment, rate);
        if (months > 0 && months < 1200) { // Max 100 years
          const years = Math.floor(months / 12);
          const remainingMonths = Math.ceil(months % 12);
          insights.push(`Payoff time: ${years} years, ${remainingMonths} months`);
          
          // Calculate total interest
          const totalInterest = (payment * months) - balance;
          if (totalInterest > 0) {
            insights.push(`Total interest: $${totalInterest.toLocaleString()}`);
          }
        }
      } catch (error) {
        // Handle calculation errors
      }
    }

    // Rate-specific insights
    if (rate < 3) {
      insights.push('✅ Excellent rate - consider investing instead of early payoff');
    } else if (rate > 15) {
      insights.push('⚠️ High rate - prioritize paying this off');
    }

    return insights;
  };

  const insights = calculateInsights();

  const handleFormSubmit = async (data: any, event?: React.BaseSyntheticEvent) => {
    // Prevent default form submission behavior
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    
    console.log('🚀 Form submission started with data:', data);
    
    try {
      // Convert form data to FinancialEntryCreate format
      const entryData: FinancialEntryCreate = {
        category: EntryCategory.LIABILITIES,
        subcategory: subcategory,
        description: getDescriptionFromData(data, subcategory),
        amount: parseFloat(data.current_balance || data.balance || '0'),
        currency: 'USD',
        frequency: FrequencyType.ONE_TIME,
        interest_rate: parseFloat(data.interest_rate || data.apr || '0'),
        loan_term_months: getLoanTermMonths(data, subcategory),
        remaining_months: getRemainingMonths(data, subcategory),
        minimum_payment: parseFloat(data.minimum_payment || data.monthly_payment || '0'),
        is_fixed_rate: data.is_fixed_rate === 'true' || data.is_fixed_rate === true,
        loan_start_date: data.purchase_date || data.first_payment_date ? 
          new Date(data.purchase_date || data.first_payment_date).toISOString() : undefined,
        original_amount: parseFloat(data.original_loan_amount || data.current_balance || '0'),
        loan_details: JSON.stringify(data), // Store all subcategory-specific data
      };

      console.log('📤 Submitting entry data:', entryData);
      await onSubmit(entryData);
      console.log('✅ Form submission successful!');
    } catch (error) {
      console.error('❌ Form submission error:', error);
      alert('Failed to submit form: ' + error);
    }
  };

  function getDescriptionFromData(data: any, subcategory: string): string {
    switch (subcategory) {
      case 'mortgage_real_estate':
        return data.description || 'Home Mortgage';
      case 'credit_cards':
        return data.card_name || 'Credit Card';
      case 'auto_loans':
        return data.vehicle_description || 'Auto Loan';
      case 'student_loans':
        return `${data.loan_servicer || 'Student'} Loan`;
      default:
        return data.description || 'Personal Loan';
    }
  }

  function getLoanTermMonths(data: any, subcategory: string): number {
    switch (subcategory) {
      case 'mortgage_real_estate':
        return (parseInt(data.loan_term_years || '0')) * 12;
      case 'auto_loans':
      case 'personal_loans':
        return parseInt(data.loan_term_months || '0');
      default:
        return 0;
    }
  }

  function getRemainingMonths(data: any, subcategory: string): number {
    switch (subcategory) {
      case 'mortgage_real_estate':
        return (parseInt(data.remaining_years || '0')) * 12;
      case 'auto_loans':
      case 'personal_loans':
        return parseInt(data.remaining_months || '0');
      default:
        return 0;
    }
  }

  // Render different forms based on subcategory
  const renderFormContent = () => {
    switch (subcategory) {
      case 'mortgage_real_estate':
        return <MortgageForm register={register} control={control} errors={errors} watch={watch} setValue={setValue} />;
      case 'credit_cards':
        return <CreditCardForm register={register} control={control} errors={errors} watch={watch} setValue={setValue} />;
      case 'auto_loans':
        return <AutoLoanForm register={register} control={control} errors={errors} watch={watch} setValue={setValue} />;
      case 'student_loans':
        return <StudentLoanForm register={register} control={control} errors={errors} watch={watch} setValue={setValue} />;
      default:
        return <PersonalLoanForm register={register} control={control} errors={errors} watch={watch} setValue={setValue} />;
    }
  };

  const getFormTitle = () => {
    const titles = {
      'mortgage_real_estate': isEditing ? 'Edit Mortgage Details' : 'Mortgage Details',
      'credit_cards': isEditing ? 'Edit Credit Card Details' : 'Credit Card Details',
      'auto_loans': isEditing ? 'Edit Auto Loan Details' : 'Auto Loan Details', 
      'student_loans': isEditing ? 'Edit Student Loan Details' : 'Student Loan Details',
      'personal_loans': isEditing ? 'Edit Personal Loan Details' : 'Personal Loan Details',
    };
    return titles[subcategory] || (isEditing ? 'Edit Loan Details' : 'Loan Details');
  };

  return (
    <Card className="max-w-4xl mx-auto">
      <Card.Header>
        <Card.Title>{getFormTitle()}</Card.Title>
        <p className="text-sm text-gray-300 mt-1">
          Enter detailed information to receive personalized financial advice
        </p>
      </Card.Header>

      <form onSubmit={(e) => { e.preventDefault(); e.stopPropagation(); }} className="space-y-6">
        {renderFormContent()}

        {/* Real-time insights */}
        {insights && insights.length > 0 && (
          <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-4">
            <h4 className="text-blue-300 font-medium flex items-center gap-2 mb-2">
              <Info className="w-4 h-4" />
              Smart Insights
            </h4>
            <div className="space-y-1">
              {insights.map((insight, index) => (
                <p key={index} className="text-sm text-blue-200">
                  {insight}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3 pt-6">
          <Button
            type="button"
            onClick={handleSubmit(handleFormSubmit)}
            isLoading={isSubmitting}
            className="flex-1 md:flex-none"
            leftIcon={<Calculator className="w-4 h-4" />}
          >
            {isEditing ? 'Update Liability' : 'Add Liability'}
          </Button>
          
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          )}
        </div>
      </form>
    </Card>
  );
};

// Individual form components for each liability type
const MortgageForm = ({ register, control, errors, watch, setValue }) => {
  const balance = parseFloat(watch('current_balance') || '0');
  const rate = parseFloat(watch('interest_rate') || '0');
  const years = parseInt(watch('loan_term_years') || '0');

  const calculatePayment = () => {
    if (balance > 0 && rate > 0 && years > 0) {
      const payment = calculateMonthlyPayment(balance, rate, years * 12);
      setValue('monthly_payment', Math.round(payment));
    }
  };

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Description *"
          placeholder="e.g., Home Loan, Primary Mortgage"
          error={errors.description?.message}
          {...register('description')}
        />
        
        <Input
          label="Current Balance *"
          type="number"
          step="0.01"
          placeholder="313,026"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.current_balance?.message}
          {...register('current_balance', { valueAsNumber: true })}
        />
      </div>

      {/* Loan Terms */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          label="Interest Rate * (%)"
          type="number"
          step="0.001"
          placeholder="2.75"
          error={errors.interest_rate?.message}
          {...register('interest_rate', { valueAsNumber: true })}
        />
        
        <Input
          label="Original Term (Years) *"
          type="number"
          placeholder="30"
          error={errors.loan_term_years?.message}
          {...register('loan_term_years', { valueAsNumber: true })}
        />
        
        <Input
          label="Years Remaining *"
          type="number"
          placeholder="15"
          error={errors.remaining_years?.message}
          {...register('remaining_years', { valueAsNumber: true })}
        />
      </div>

      {/* Payment Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex gap-2">
          <Input
            label="Monthly Payment"
            type="number"
            step="0.01"
            placeholder="2,264"
            leftIcon={<DollarSign className="w-4 h-4" />}
            error={errors.monthly_payment?.message}
            {...register('monthly_payment', { valueAsNumber: true })}
          />
          <Button
            type="button"
            variant="outline"
            onClick={calculatePayment}
            className="mt-6 px-3"
            title="Calculate payment"
          >
            <Calculator className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-200">
            Rate Type
          </label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="true"
                {...register('is_fixed_rate')}
                className="mr-2"
                defaultChecked
              />
              Fixed Rate
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="false"
                {...register('is_fixed_rate')}
                className="mr-2"
              />
              Variable Rate
            </label>
          </div>
        </div>
      </div>

      {/* Property Information */}
      <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-200 mb-3">Property Information (Optional)</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Property Value"
            type="number"
            step="0.01"
            placeholder="1,050,000"
            leftIcon={<DollarSign className="w-4 h-4" />}
            error={errors.property_value?.message}
            {...register('property_value', { valueAsNumber: true })}
          />
          
          <Input
            label="Purchase Date"
            type="date"
            error={errors.purchase_date?.message}
            {...register('purchase_date')}
          />
        </div>

        <div className="mt-4 space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              {...register('escrow_included')}
              className="mr-2"
            />
            <span className="text-sm text-gray-200">Escrow included (taxes, insurance)</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              {...register('tax_deductible')}
              className="mr-2"
              defaultChecked
            />
            <span className="text-sm text-gray-200">Interest is tax deductible</span>
          </label>
        </div>
      </div>
    </div>
  );
};

const CreditCardForm = ({ register, control, errors, watch }) => {
  const balance = parseFloat(watch('current_balance') || '0');
  const limit = parseFloat(watch('credit_limit') || '0');
  const utilization = limit > 0 ? (balance / limit * 100).toFixed(1) : '0';

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Card Name *"
          placeholder="e.g., Chase Sapphire, Capital One"
          error={errors.card_name?.message}
          {...register('card_name')}
        />
        
        <Input
          label="Current Balance *"
          type="number"
          step="0.01"
          placeholder="971"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.current_balance?.message}
          {...register('current_balance', { valueAsNumber: true })}
        />
      </div>

      {/* Credit Limit and Rates */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          label="Credit Limit *"
          type="number"
          step="0.01"
          placeholder="15,000"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.credit_limit?.message}
          {...register('credit_limit', { valueAsNumber: true })}
        />
        
        <Input
          label="APR * (%)"
          type="number"
          step="0.01"
          placeholder="22.99"
          error={errors.apr?.message}
          {...register('apr', { valueAsNumber: true })}
        />
        
        <div className="flex flex-col">
          <label className="text-sm font-medium text-gray-200 mb-1">
            Utilization Rate
          </label>
          <div className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-sm">
            {utilization}%
            {parseFloat(utilization) > 30 && (
              <span className="text-red-400 ml-2">High</span>
            )}
          </div>
        </div>
      </div>

      {/* Payment Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Minimum Payment"
          type="number"
          step="0.01"
          placeholder="30"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.minimum_payment?.message}
          {...register('minimum_payment', { valueAsNumber: true })}
        />
        
        <Input
          label="Average Monthly Payment"
          type="number"
          step="0.01"
          placeholder="200"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.average_monthly_payment?.message}
          {...register('average_monthly_payment', { valueAsNumber: true })}
        />
      </div>

      {/* Additional Features */}
      <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-200 mb-3">Additional Details (Optional)</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Intro APR (%)"
            type="number"
            step="0.01"
            placeholder="0"
            error={errors.intro_apr?.message}
            {...register('intro_apr', { valueAsNumber: true })}
          />
          
          <Input
            label="Intro APR End Date"
            type="date"
            error={errors.intro_apr_end_date?.message}
            {...register('intro_apr_end_date')}
          />
        </div>

        <div className="mt-4">
          <Controller
            name="rewards_type"
            control={control}
            render={({ field }) => (
              <Select
                label="Rewards Type"
                options={[
                  { value: '', label: 'No rewards' },
                  { value: 'cashback', label: 'Cashback' },
                  { value: 'points', label: 'Points' },
                  { value: 'miles', label: 'Miles' },
                ]}
                {...field}
              />
            )}
          />
        </div>
      </div>
    </div>
  );
};

const AutoLoanForm = ({ register, control, errors, watch, setValue }) => {
  const balance = parseFloat(watch('current_balance') || '0');
  const originalAmount = parseFloat(watch('original_loan_amount') || '0');
  const rate = parseFloat(watch('interest_rate') || '0');
  const months = parseInt(watch('loan_term_months') || '0');

  const calculatePayment = () => {
    if (originalAmount > 0 && rate > 0 && months > 0) {
      const payment = calculateMonthlyPayment(originalAmount, rate, months);
      setValue('monthly_payment', Math.round(payment));
    }
  };

  return (
    <div className="space-y-6">
      {/* Vehicle Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Vehicle Description *"
          placeholder="e.g., 2021 Tesla Model 3"
          error={errors.vehicle_description?.message}
          {...register('vehicle_description')}
        />
        
        <Input
          label="Current Balance *"
          type="number"
          step="0.01"
          placeholder="25,000"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.current_balance?.message}
          {...register('current_balance', { valueAsNumber: true })}
        />
      </div>

      {/* Loan Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          label="Original Loan Amount *"
          type="number"
          step="0.01"
          placeholder="45,000"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.original_loan_amount?.message}
          {...register('original_loan_amount', { valueAsNumber: true })}
        />
        
        <Input
          label="Interest Rate * (%)"
          type="number"
          step="0.01"
          placeholder="3.5"
          error={errors.interest_rate?.message}
          {...register('interest_rate', { valueAsNumber: true })}
        />
        
        <Input
          label="Loan Term (Months) *"
          type="number"
          placeholder="60"
          error={errors.loan_term_months?.message}
          {...register('loan_term_months', { valueAsNumber: true })}
        />
      </div>

      {/* Payment and Time */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex gap-2">
          <Input
            label="Monthly Payment *"
            type="number"
            step="0.01"
            placeholder="812"
            leftIcon={<DollarSign className="w-4 h-4" />}
            error={errors.monthly_payment?.message}
            {...register('monthly_payment', { valueAsNumber: true })}
          />
          <Button
            type="button"
            variant="outline"
            onClick={calculatePayment}
            className="mt-6 px-3"
            title="Calculate payment"
          >
            <Calculator className="w-4 h-4" />
          </Button>
        </div>
        
        <Input
          label="Months Remaining *"
          type="number"
          placeholder="36"
          error={errors.remaining_months?.message}
          {...register('remaining_months', { valueAsNumber: true })}
        />
      </div>

      {/* Vehicle Details */}
      <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-200 mb-3">Vehicle Details (Optional)</h4>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Input
            label="Current Value"
            type="number"
            step="0.01"
            placeholder="30,000"
            leftIcon={<DollarSign className="w-4 h-4" />}
            error={errors.vehicle_value?.message}
            {...register('vehicle_value', { valueAsNumber: true })}
          />
          
          <Input
            label="Year"
            type="number"
            placeholder="2021"
            error={errors.vehicle_year?.message}
            {...register('vehicle_year', { valueAsNumber: true })}
          />
          
          <Input
            label="Make"
            placeholder="Tesla"
            error={errors.vehicle_make?.message}
            {...register('vehicle_make')}
          />
          
          <Input
            label="Model"
            placeholder="Model 3"
            error={errors.vehicle_model?.message}
            {...register('vehicle_model')}
          />
        </div>
      </div>
    </div>
  );
};

const StudentLoanForm = ({ register, control, errors }) => {
  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Loan Servicer *"
          placeholder="e.g., Navient, Great Lakes"
          error={errors.loan_servicer?.message}
          {...register('loan_servicer')}
        />
        
        <Input
          label="Current Balance *"
          type="number"
          step="0.01"
          placeholder="35,000"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.current_balance?.message}
          {...register('current_balance', { valueAsNumber: true })}
        />
      </div>

      {/* Loan Terms */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          label="Monthly Payment *"
          type="number"
          step="0.01"
          placeholder="350"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.monthly_payment?.message}
          {...register('monthly_payment', { valueAsNumber: true })}
        />
        
        <Input
          label="Interest Rate * (%)"
          type="number"
          step="0.01"
          placeholder="4.5"
          error={errors.interest_rate?.message}
          {...register('interest_rate', { valueAsNumber: true })}
        />
        
        <Controller
          name="loan_type"
          control={control}
          render={({ field }) => (
            <Select
              label="Loan Type *"
              options={[
                { value: 'federal', label: 'Federal' },
                { value: 'private', label: 'Private' },
              ]}
              error={errors.loan_type?.message}
              {...field}
            />
          )}
        />
      </div>

      {/* Federal Loan Specifics */}
      <div className="bg-gray-800/50 border border-gray-600 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-200 mb-3">Federal Loan Details (Optional)</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <Input
            label="Repayment Plan"
            placeholder="e.g., Income-Driven, Standard"
            error={errors.repayment_plan?.message}
            {...register('repayment_plan')}
          />
        </div>

        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              {...register('subsidized')}
              className="mr-2"
            />
            <span className="text-sm text-gray-200">Subsidized loan</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              {...register('eligible_for_forgiveness')}
              className="mr-2"
            />
            <span className="text-sm text-gray-200">Eligible for loan forgiveness</span>
          </label>
        </div>
      </div>

      {/* Important Dates */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          label="Graduation Date"
          type="date"
          error={errors.graduation_date?.message}
          {...register('graduation_date')}
        />
        
        <Input
          label="First Payment Date"
          type="date"
          error={errors.first_payment_date?.message}
          {...register('first_payment_date')}
        />
        
        <Input
          label="Expected Payoff Date"
          type="date"
          error={errors.expected_payoff_date?.message}
          {...register('expected_payoff_date')}
        />
      </div>
    </div>
  );
};

const PersonalLoanForm = ({ register, control, errors, watch, setValue }) => {
  const balance = parseFloat(watch('current_balance') || '0');
  const rate = parseFloat(watch('interest_rate') || '0');
  const months = parseInt(watch('loan_term_months') || '0');

  const calculatePayment = () => {
    if (balance > 0 && rate > 0 && months > 0) {
      const payment = calculateMonthlyPayment(balance, rate, months);
      setValue('monthly_payment', Math.round(payment));
    }
  };

  return (
    <div className="space-y-6">
      {/* Basic Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Description *"
          placeholder="e.g., Personal Loan, Debt Consolidation"
          error={errors.description?.message}
          {...register('description')}
        />
        
        <Input
          label="Current Balance *"
          type="number"
          step="0.01"
          placeholder="10,000"
          leftIcon={<DollarSign className="w-4 h-4" />}
          error={errors.current_balance?.message}
          {...register('current_balance', { valueAsNumber: true })}
        />
      </div>

      {/* Loan Terms */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input
          label="Interest Rate * (%)"
          type="number"
          step="0.01"
          placeholder="8.5"
          error={errors.interest_rate?.message}
          {...register('interest_rate', { valueAsNumber: true })}
        />
        
        <Input
          label="Loan Term (Months) *"
          type="number"
          placeholder="36"
          error={errors.loan_term_months?.message}
          {...register('loan_term_months', { valueAsNumber: true })}
        />
        
        <Input
          label="Months Remaining *"
          type="number"
          placeholder="24"
          error={errors.remaining_months?.message}
          {...register('remaining_months', { valueAsNumber: true })}
        />
      </div>

      {/* Payment */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex gap-2">
          <Input
            label="Monthly Payment *"
            type="number"
            step="0.01"
            placeholder="315"
            leftIcon={<DollarSign className="w-4 h-4" />}
            error={errors.monthly_payment?.message}
            {...register('monthly_payment', { valueAsNumber: true })}
          />
          <Button
            type="button"
            variant="outline"
            onClick={calculatePayment}
            className="mt-6 px-3"
            title="Calculate payment"
          >
            <Calculator className="w-4 h-4" />
          </Button>
        </div>

        <Controller
          name="purpose"
          control={control}
          render={({ field }) => (
            <Select
              label="Purpose"
              options={[
                { value: '', label: 'Not specified' },
                { value: 'debt_consolidation', label: 'Debt Consolidation' },
                { value: 'home_improvement', label: 'Home Improvement' },
                { value: 'medical', label: 'Medical Expenses' },
                { value: 'vacation', label: 'Vacation' },
                { value: 'other', label: 'Other' },
              ]}
              {...field}
            />
          )}
        />
      </div>

      {/* Loan Type */}
      <div className="space-y-2">
        <label className="flex items-center">
          <input
            type="checkbox"
            {...register('secured')}
            className="mr-2"
          />
          <span className="text-sm text-gray-200">Secured loan (backed by collateral)</span>
        </label>
      </div>
    </div>
  );
};

export default SmartLiabilityForm;