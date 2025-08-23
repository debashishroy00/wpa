/**
 * WealthPath AI - Structured Financial Entry System
 * Architecture Lead Directive: Organized category-based entry system with visual hierarchy
 */
import React, { useState, useMemo } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Home,
  Briefcase,
  CreditCard,
  PiggyBank,
  Car,
  ShoppingCart,
  Coffee,
  Plus,
  ChevronDown,
  ChevronRight,
  Edit3,
  Trash2,
  Target,
  Zap,
  Heart
} from 'lucide-react';

import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { 
  FinancialEntry, 
  EntryCategory, 
  FrequencyType,
} from '../../types/financial';
import { 
  useCategorizedEntriesQuery, 
  useDeleteFinancialEntryMutation 
} from '../../hooks/use-financial-queries';
// Profile queries removed - StructuredEntrySystem only handles financial data

interface StructuredEntrySystemProps {
  onAddEntry?: (category?: EntryCategory, subcategory?: string) => void;
  onEditEntry?: (entry: FinancialEntry) => void;
}

// Category definitions with improved personal vs business organization
const ASSET_CATEGORIES = [
  {
    name: 'Cash & Bank Accounts',
    icon: DollarSign,
    color: 'green',
    subcategories: ['Checking Account', 'Savings Account', 'Money Market Account', 'Certificate of Deposit', 'Checking Offshore']
  },
  {
    name: 'Investment Accounts',
    icon: TrendingUp,
    color: 'purple', 
    subcategories: ['Brokerage Account', 'Individual Stocks', 'Mutual Funds', 'ETFs', 'Bonds', 'Cryptocurrency']
  },
  {
    name: 'Retirement Accounts', 
    icon: Target,
    color: 'blue',
    subcategories: ['401k Account', 'Traditional IRA', 'Roth IRA', 'SEP-IRA', 'Pension', '403b']
  },
  {
    name: 'Real Estate',
    icon: Home,
    color: 'emerald',
    subcategories: ['Primary Residence', 'Rental Property', 'Vacation Home', 'Land', 'REITs']
  },
  {
    name: 'Personal Property',
    icon: Heart,
    color: 'pink',
    subcategories: ['Jewelry', 'Art & Collectibles', 'Vehicles', 'Electronics', 'Furniture', 'Other Valuables']
  },
  {
    name: 'Business Assets',
    icon: Briefcase,
    color: 'indigo',
    subcategories: ['Business Checking', 'Business Equipment', 'Business Real Estate', 'Business Investments', 'Inventory', 'Accounts Receivable']
  },
  {
    name: 'Other Assets',
    icon: PiggyBank,
    color: 'gray',
    subcategories: ['Other Investment', 'Miscellaneous Assets', 'Digital Assets', 'Intellectual Property']
  }
];

const LIABILITY_CATEGORIES = [
  {
    name: 'Mortgage & Real Estate',
    icon: Home,
    color: 'red',
    subcategories: ['Primary Mortgage', 'Investment Property Loan', 'HELOC', 'Home Equity Loan']
  },
  {
    name: 'Credit Cards',
    icon: CreditCard,
    color: 'orange',
    subcategories: ['Personal Credit Cards', 'Business Credit Cards', 'Store Cards']
  },
  {
    name: 'Loans',
    icon: Car,
    color: 'yellow',
    subcategories: ['Auto Loan', 'Personal Loan', 'Student Loans', 'Business Loans']
  }
];

const INCOME_CATEGORIES = [
  {
    name: 'Employment Income',
    icon: Briefcase,
    color: 'blue',
    subcategories: ['Salary', 'Hourly Wages', 'Bonus', 'Commission', 'Stock Options', 'Benefits']
  },
  {
    name: 'Investment Income',
    icon: TrendingUp,
    color: 'green',
    subcategories: ['Dividends', 'Interest', 'Capital Gains', 'Rental Income', 'Crypto Gains']
  },
  {
    name: 'Business Income',
    icon: DollarSign,
    color: 'purple',
    subcategories: ['Self-Employment', 'Consulting', 'Side Hustle', 'Passive Income']
  }
];

const EXPENSE_CATEGORIES = [
  {
    name: 'Housing',
    icon: Home,
    color: 'blue',
    subcategories: ['Rent', 'Mortgage', 'Property Tax', 'HOA', 'Home Insurance', 'Maintenance', 'Repairs']
  },
  {
    name: 'Utilities',
    icon: Zap,
    color: 'yellow',
    subcategories: ['Electricity', 'Gas', 'Water', 'Internet', 'Phone', 'Trash', 'Sewer']
  },
  {
    name: 'Transportation',
    icon: Car,
    color: 'green',
    subcategories: ['Car Payment', 'Gas', 'Car Insurance', 'Maintenance', 'Public Transit', 'Uber/Lyft']
  },
  {
    name: 'Food & Dining',
    icon: Coffee,
    color: 'orange',
    subcategories: ['Groceries', 'Restaurants', 'Coffee', 'Meal Delivery', 'Work Meals']
  },
  {
    name: 'Healthcare',
    icon: Heart,
    color: 'red',
    subcategories: ['Health Insurance', 'Doctor Visits', 'Medications', 'Dental', 'Vision', 'Mental Health']
  },
  {
    name: 'Personal',
    icon: ShoppingCart,
    color: 'purple',
    subcategories: ['Shopping', 'Clothing', 'Personal Care', 'Subscriptions', 'Entertainment', 'Travel']
  }
];

// Profile categories removed - now handled by ProfileManagementPage

// Benefits and Tax categories removed - now handled by ProfileManagementPage

const StructuredEntrySystem: React.FC<StructuredEntrySystemProps> = ({
  onAddEntry,
  onEditEntry
}) => {
  const [activeTab, setActiveTab] = useState<EntryCategory>(EntryCategory.ASSETS);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['Real Estate', 'Retirement Accounts']));
  
  const { data: categorizedData, isLoading, refetch } = useCategorizedEntriesQuery();
  const deleteMutation = useDeleteFinancialEntryMutation();
  
  // Profile data queries removed - StructuredEntrySystem only handles financial data

  // Debug logging
  console.log('🏗️ StructuredEntrySystem - Categorized Data:', categorizedData);
  console.log('🏗️ StructuredEntrySystem - Asset Categories:', categorizedData?.categories?.assets);
  // Profile debug logging removed

  // Extract entries from the new backend categorized structure
  const allEntries = categorizedData?.categories ? [
    // Assets from new subcategory structure
    ...(categorizedData.categories.assets?.cash_bank_accounts || []),
    ...(categorizedData.categories.assets?.investment_accounts || []),
    ...(categorizedData.categories.assets?.retirement_accounts || []),
    ...(categorizedData.categories.assets?.real_estate || []),
    ...(categorizedData.categories.assets?.personal_property || []),
    ...(categorizedData.categories.assets?.business_assets || []),
    ...(categorizedData.categories.assets?.other_assets || []),
    // Liabilities from new subcategory structure
    ...(categorizedData.categories.liabilities?.mortgage_real_estate || []),
    ...(categorizedData.categories.liabilities?.credit_cards || []),
    ...(categorizedData.categories.liabilities?.auto_loans || []),
    ...(categorizedData.categories.liabilities?.student_loans || []),
    ...(categorizedData.categories.liabilities?.personal_loans || []),
    ...(categorizedData.categories.liabilities?.other_debt || []),
    // Income from new subcategory structure
    ...(categorizedData.categories.income?.employment_income || []),
    ...(categorizedData.categories.income?.business_income || []),
    ...(categorizedData.categories.income?.investment_income || []),
    ...(categorizedData.categories.income?.rental_income || []),
    ...(categorizedData.categories.income?.passive_income || []),
    ...(categorizedData.categories.income?.other_income || []),
    // Expenses from new subcategory structure
    ...(categorizedData.categories.expenses?.housing || []),
    ...(categorizedData.categories.expenses?.utilities || []),
    ...(categorizedData.categories.expenses?.transportation || []),
    ...(categorizedData.categories.expenses?.food || []),
    ...(categorizedData.categories.expenses?.healthcare || []),
    ...(categorizedData.categories.expenses?.personal || []),
    ...(categorizedData.categories.expenses?.other_expenses || [])
  ] : [];

  // Organize entries by category and subcategory
  const organizedEntries = useMemo(() => {
    const organized: { [key: string]: { [subcat: string]: FinancialEntry[] } } = {};
    
    allEntries.forEach(entry => {
      const category = entry.subcategory || 'Other';
      if (!organized[category]) {
        organized[category] = {};
      }
      const subcat = entry.subcategory || 'General';
      if (!organized[category][subcat]) {
        organized[category][subcat] = [];
      }
      organized[category][subcat].push(entry);
    });
    
    return organized;
  }, [allEntries]);

  // Calculate totals by category (using new backend structure)
  const calculateTotals = (category: EntryCategory) => {
    if (!categorizedData?.categories) return { total: 0, count: 0 };
    
    let categoryEntries: any[] = [];
    switch (category) {
      case EntryCategory.ASSETS:
        // Aggregate all asset subcategories
        const assetCategories = categorizedData.categories.assets;
        categoryEntries = [
          ...(assetCategories.cash_bank_accounts || []),
          ...(assetCategories.investment_accounts || []),
          ...(assetCategories.retirement_accounts || []),
          ...(assetCategories.real_estate || []),
          ...(assetCategories.personal_property || []),
          ...(assetCategories.business_assets || []),
          ...(assetCategories.other_assets || [])
        ];
        break;
      case EntryCategory.LIABILITIES:
        // Aggregate all liability subcategories
        const liabilityCategories = categorizedData.categories.liabilities;
        categoryEntries = [
          ...(liabilityCategories.mortgage_real_estate || []),
          ...(liabilityCategories.credit_cards || []),
          ...(liabilityCategories.auto_loans || []),
          ...(liabilityCategories.student_loans || []),
          ...(liabilityCategories.personal_loans || []),
          ...(liabilityCategories.other_debt || [])
        ];
        break;
      case EntryCategory.INCOME:
        // Aggregate all income subcategories
        const incomeCategories = categorizedData.categories.income;
        categoryEntries = [
          ...(incomeCategories.employment_income || []),
          ...(incomeCategories.business_income || []),
          ...(incomeCategories.investment_income || []),
          ...(incomeCategories.rental_income || []),
          ...(incomeCategories.passive_income || []),
          ...(incomeCategories.other_income || [])
        ];
        break;
      case EntryCategory.EXPENSES:
        // Aggregate all expense subcategories
        const expenseCategories = categorizedData.categories.expenses;
        categoryEntries = [
          ...(expenseCategories.housing || []),
          ...(expenseCategories.utilities || []),
          ...(expenseCategories.transportation || []),
          ...(expenseCategories.food || []),
          ...(expenseCategories.healthcare || []),
          ...(expenseCategories.personal || []),
          ...(expenseCategories.other_expenses || [])
        ];
        break;
      // Profile categories removed - handled by ProfileManagementPage
    }
    
    const total = categoryEntries.reduce((sum, entry) => sum + entry.amount, 0);
    
    return {
      total,
      count: categoryEntries.length
    };
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleClearProfileField = async (entry: FinancialEntry) => {
    // Import the profile API functions
    const { profileApi } = await import('../../utils/profile-api');
    
    // Create an update payload to clear the specific field
    let updateData: any = {};
    
    switch (entry.id) {
      case 'profile-age':
        updateData.age = null;
        break;
      case 'profile-state':
        updateData.state = null;
        break;
      case 'profile-notes':
        updateData.notes = null;
        break;
      case 'profile-marital':
        updateData.marital_status = null;
        break;
      case 'profile-employment':
        updateData.employment_status = null;
        break;
      case 'profile-occupation':
        updateData.occupation = null;
        break;
      case 'profile-gender':
        updateData.gender = null;
        break;
      case 'profile-phone':
        updateData.phone = null;
        break;
      case 'profile-city':
        updateData.city = null;
        break;
      case 'profile-risk':
        updateData.risk_tolerance = null;
        break;
      default:
        throw new Error(`Unknown profile field: ${entry.id}`);
    }
    
    console.log('🔄 Clearing profile field:', entry.id, 'with data:', updateData);
    return profileApi.updateProfile(updateData);
  };

  const handleDeleteEntry = async (entry: FinancialEntry) => {
    console.log('🗑️ Delete button clicked for entry:', entry);
    console.log('🗑️ Entry ID:', entry.id, 'Type:', typeof entry.id);
    
    // Check if this is a profile entry (synthetic ID starting with 'profile-')
    if (typeof entry.id === 'string' && entry.id.startsWith('profile-')) {
      console.log('🗑️ Handling profile entry deletion/clearing');
      
      if (window.confirm(`Are you sure you want to clear "${entry.description}" from your profile?`)) {
        try {
          // For profile entries, we'll clear the specific field
          await handleClearProfileField(entry);
          console.log('✅ Profile field cleared successfully');
          refetch(); // Refresh the data
        } catch (error: any) {
          console.error('❌ Failed to clear profile field:', error);
          alert('Failed to clear profile field. Please try again.');
        }
      }
      return;
    }
    
    if (window.confirm(`Are you sure you want to delete "${entry.description}"?`)) {
      try {
        console.log('🗑️ Deleting entry with ID:', entry.id);
        
        // Check if user is authenticated
        const authTokens = localStorage.getItem('auth_tokens');
        console.log('🔐 Auth tokens present:', !!authTokens);
        
        // Ensure we have a valid numeric ID for financial entries
        const entryId = parseInt(entry.id);
        if (isNaN(entryId)) {
          throw new Error(`Invalid entry ID: ${entry.id}`);
        }
        
        const result = await deleteMutation.mutateAsync(entryId);
        console.log('✅ Delete successful:', result);
        
        // Refetch the data instead of reloading the page
        refetch();
      } catch (error: any) {
        console.error('❌ Failed to delete entry:', error);
        
        // More detailed error message
        let errorMessage = 'Failed to delete entry: ';
        if (error?.status_code === 401) {
          errorMessage += 'Not authenticated. Please log in again.';
        } else if (error?.status_code === 404) {
          errorMessage += 'Entry not found. It may have already been deleted.';
          // Still refetch to update the list
          refetch();
        } else if (error?.detail) {
          errorMessage += error.detail;
        } else if (error instanceof Error) {
          errorMessage += error.message;
        } else {
          errorMessage += 'Unknown error';
        }
        
        alert(errorMessage);
      }
    }
  };

  const toggleCategory = (categoryName: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryName)) {
      newExpanded.delete(categoryName);
    } else {
      newExpanded.add(categoryName);
    }
    setExpandedCategories(newExpanded);
  };

  const renderCategoryPanel = (categories: any[], categoryType: EntryCategory) => {
    const categoryTotal = calculateTotals(categoryType);

    return (
      <div className="space-y-6">
        {/* Quick Stats Header */}
        <div className="bg-gradient-to-r from-gray-800 to-gray-700 p-6 rounded-xl">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-white">
              {categoryType.charAt(0).toUpperCase() + categoryType.slice(1)} Overview
            </h3>
            <Button
              onClick={() => onAddEntry?.(categoryType)}
              size="sm"
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add {
                categoryType === EntryCategory.PROFILE ? 'Profile' :
                categoryType === EntryCategory.BENEFITS ? 'Benefit' :
                categoryType === EntryCategory.TAX_INFO ? 'Tax Info' :
                categoryType === EntryCategory.ASSETS ? 'Asset' :
                categoryType === EntryCategory.LIABILITIES ? 'Liability' :
                categoryType === EntryCategory.INCOME ? 'Income' :
                categoryType === EntryCategory.EXPENSES ? 'Expense' :
                categoryType.slice(0, -1)
              }
            </Button>
          </div>
          
          <div className="grid grid-cols-3 gap-4 text-center">
            <div className="bg-gray-700 rounded-lg p-4">
              <div className={`text-2xl font-bold ${
                categoryType === EntryCategory.ASSETS || categoryType === EntryCategory.INCOME
                  ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatCurrency(categoryTotal.total)}
              </div>
              <div className="text-sm text-gray-200 font-medium">Total Value</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-400">{categoryTotal.count}</div>
              <div className="text-sm text-gray-200 font-medium">Entries</div>
            </div>
            <div className="bg-gray-700 rounded-lg p-4">
              <div className="text-2xl font-bold text-yellow-400">
                {categories.length}
              </div>
              <div className="text-sm text-gray-200 font-medium">Categories</div>
            </div>
          </div>
        </div>

        {/* Category Sections */}
        <div className="space-y-4">
          {categories.map((category) => {
            const Icon = category.icon;
            // Get entries from the specific subcategory based on category name
            let subCategoryEntries: any[] = [];
            if (categorizedData?.categories) {
              switch (categoryType) {
                case EntryCategory.ASSETS:
                  if (category.name === 'Cash & Bank Accounts') {
                    subCategoryEntries = categorizedData.categories.assets?.cash_bank_accounts || [];
                  } else if (category.name === 'Investment Accounts') {
                    subCategoryEntries = categorizedData.categories.assets?.investment_accounts || [];
                  } else if (category.name === 'Retirement Accounts') {
                    subCategoryEntries = categorizedData.categories.assets?.retirement_accounts || [];
                  } else if (category.name === 'Real Estate') {
                    subCategoryEntries = categorizedData.categories.assets?.real_estate || [];
                  } else if (category.name === 'Personal Property') {
                    subCategoryEntries = categorizedData.categories.assets?.personal_property || [];
                  } else if (category.name === 'Business Assets') {
                    subCategoryEntries = categorizedData.categories.assets?.business_assets || [];
                  } else if (category.name === 'Other Assets') {
                    subCategoryEntries = categorizedData.categories.assets?.other_assets || [];
                  } else {
                    subCategoryEntries = categorizedData.categories.assets?.other_assets || [];
                  }
                  break;
                case EntryCategory.EXPENSES:
                  // For expenses, use the new subcategory structure
                  if (category.name === 'Housing') {
                    subCategoryEntries = categorizedData.categories.expenses?.housing || [];
                  } else if (category.name === 'Utilities') {
                    subCategoryEntries = categorizedData.categories.expenses?.utilities || [];
                  } else if (category.name === 'Transportation') {
                    subCategoryEntries = categorizedData.categories.expenses?.transportation || [];
                  } else if (category.name === 'Food & Dining') {
                    subCategoryEntries = categorizedData.categories.expenses?.food || [];
                  } else if (category.name === 'Healthcare') {
                    subCategoryEntries = categorizedData.categories.expenses?.healthcare || [];
                  } else if (category.name === 'Personal') {
                    subCategoryEntries = categorizedData.categories.expenses?.personal || [];
                  } else {
                    subCategoryEntries = categorizedData.categories.expenses?.other_expenses || [];
                  }
                  break;
                case EntryCategory.LIABILITIES:
                  // For liabilities, use the new subcategory structure
                  if (category.name === 'Mortgage & Real Estate') {
                    subCategoryEntries = categorizedData.categories.liabilities?.mortgage_real_estate || [];
                  } else if (category.name === 'Credit Cards') {
                    subCategoryEntries = categorizedData.categories.liabilities?.credit_cards || [];
                  } else if (category.name === 'Loans') {
                    subCategoryEntries = [
                      ...(categorizedData.categories.liabilities?.auto_loans || []),
                      ...(categorizedData.categories.liabilities?.student_loans || []),
                      ...(categorizedData.categories.liabilities?.personal_loans || [])
                    ];
                  } else {
                    subCategoryEntries = categorizedData.categories.liabilities?.other_debt || [];
                  }
                  break;
                case EntryCategory.INCOME:
                  // For income, use the new subcategory structure
                  if (category.name === 'Employment Income') {
                    subCategoryEntries = categorizedData.categories.income?.employment_income || [];
                  } else if (category.name === 'Investment Income') {
                    subCategoryEntries = categorizedData.categories.income?.investment_income || [];
                  } else if (category.name === 'Business Income') {
                    subCategoryEntries = categorizedData.categories.income?.business_income || [];
                  } else {
                    subCategoryEntries = categorizedData.categories.income?.other_income || [];
                  }
                  break;
                case EntryCategory.PROFILE:
                  // Convert profile data to display format based on specific subcategory
                  if (profileData?.profile) {
                    const profile = profileData.profile;
                    subCategoryEntries = [];
                    
                    // Only show relevant fields for each subcategory
                    if (category.name === 'Personal Information') {
                      if (profile.age) {
                        subCategoryEntries.push({
                          id: 'profile-age',
                          description: 'Age',
                          amount: 0,
                          notes: profile.age.toString(),
                          frequency: 'one_time'
                        });
                      }
                      if (profile.gender) {
                        subCategoryEntries.push({
                          id: 'profile-gender',
                          description: 'Gender',
                          amount: 0,
                          notes: profile.gender,
                          frequency: 'one_time'
                        });
                      }
                      if (profile.marital_status) {
                        subCategoryEntries.push({
                          id: 'profile-marital',
                          description: 'Marital Status',
                          amount: 0,
                          notes: profile.marital_status,
                          frequency: 'one_time'
                        });
                      }
                      if (profile.notes) {
                        subCategoryEntries.push({
                          id: 'profile-notes',
                          description: 'Name',
                          amount: 0,
                          notes: profile.notes.replace('Name: ', ''),
                          frequency: 'one_time'
                        });
                      }
                    } else if (category.name === 'Contact & Location') {
                      if (profile.state) {
                        subCategoryEntries.push({
                          id: 'profile-state',
                          description: 'State',
                          amount: 0,
                          notes: profile.state,
                          frequency: 'one_time'
                        });
                      }
                      if (profile.city) {
                        subCategoryEntries.push({
                          id: 'profile-city',
                          description: 'City',
                          amount: 0,
                          notes: profile.city,
                          frequency: 'one_time'
                        });
                      }
                      if (profile.phone) {
                        subCategoryEntries.push({
                          id: 'profile-phone',
                          description: 'Phone',
                          amount: 0,
                          notes: profile.phone,
                          frequency: 'one_time'
                        });
                      }
                    } else if (category.name === 'Employment') {
                      if (profile.employment_status) {
                        subCategoryEntries.push({
                          id: 'profile-employment',
                          description: 'Employment Status',
                          amount: 0,
                          notes: profile.employment_status,
                          frequency: 'one_time'
                        });
                      }
                      if (profile.occupation) {
                        subCategoryEntries.push({
                          id: 'profile-occupation',
                          description: 'Occupation',
                          amount: 0,
                          notes: profile.occupation,
                          frequency: 'one_time'
                        });
                      }
                    } else if (category.name === 'Investment Profile') {
                      if (profile.risk_tolerance) {
                        subCategoryEntries.push({
                          id: 'profile-risk',
                          description: 'Risk Tolerance',
                          amount: 0,
                          notes: profile.risk_tolerance,
                          frequency: 'one_time'
                        });
                      }
                    } else if (category.name === 'Spouse/Partner') {
                      // Show family members data for spouse category
                      console.log('🏗️ Building spouse entries, familyData:', familyData);
                      if (familyData && Array.isArray(familyData)) {
                        const spouses = familyData.filter(member => 
                          member.relationship_type === 'spouse' || member.relationship_type === 'partner'
                        );
                        console.log('🏗️ Found spouses:', spouses);
                        subCategoryEntries = spouses.map(spouse => ({
                          id: `family-${spouse.id}`,
                          description: spouse.name || 'Spouse',
                          amount: spouse.income || 0,
                          notes: spouse.age ? `Age: ${spouse.age}` : (spouse.notes || 'No details'),
                          frequency: 'annual'
                        }));
                        console.log('🏗️ Spouse entries created:', subCategoryEntries);
                      } else {
                        console.log('🏗️ No family data available for spouse section');
                      }
                    } else if (category.name === 'Dependents') {
                      // Show family members data for dependents category
                      console.log('🏗️ Building dependent entries, familyData:', familyData);
                      if (familyData && Array.isArray(familyData)) {
                        const dependents = familyData.filter(member => 
                          member.relationship_type === 'child' || 
                          member.relationship_type === 'dependent' ||
                          member.relationship_type === 'other_dependent'
                        );
                        console.log('🏗️ Found dependents:', dependents);
                        subCategoryEntries = dependents.map(dependent => ({
                          id: `family-${dependent.id}`,
                          description: dependent.name || 'Dependent',
                          amount: dependent.education_fund_target || 0,
                          notes: dependent.age ? `Age: ${dependent.age}` : (dependent.notes || 'No details'),
                          frequency: 'one_time'
                        }));
                        console.log('🏗️ Dependent entries created:', subCategoryEntries);
                      } else {
                        console.log('🏗️ No family data available for dependents section');
                      }
                    }
                  }
                  break;
                case EntryCategory.BENEFITS:
                  // Convert benefits data to display format
                  if (benefitsData && Array.isArray(benefitsData)) {
                    subCategoryEntries = benefitsData.map(benefit => ({
                      id: `benefit-${benefit.id}`,
                      description: benefit.benefit_name || benefit.benefit_type,
                      amount: benefit.estimated_monthly_benefit || 0,
                      notes: benefit.notes || '',
                      frequency: 'monthly'
                    }));
                  }
                  break;
                case EntryCategory.TAX_INFO:
                  // Convert tax data to display format
                  if (taxData && Array.isArray(taxData)) {
                    subCategoryEntries = taxData.map(tax => ({
                      id: `tax-${tax.id}`,
                      description: `Tax Year ${tax.tax_year}`,
                      amount: tax.adjusted_gross_income || 0,
                      notes: `${tax.federal_tax_bracket || 0}% tax bracket`,
                      frequency: 'annually'
                    }));
                  }
                  break;
                default:
                  subCategoryEntries = [];
              }
            }
            
            const categorySubtotal = subCategoryEntries.reduce((sum, entry) => sum + entry.amount, 0);
            const isExpanded = expandedCategories.has(category.name);

            return (
              <Card key={category.name} className="overflow-hidden">
                {/* Category Header */}
                <div 
                  className={`p-4 bg-${category.color}-900/10 border-b border-gray-700 cursor-pointer hover:bg-${category.color}-900/20 transition-colors`}
                  onClick={() => toggleCategory(category.name)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      {isExpanded ? 
                        <ChevronDown className="w-5 h-5 text-gray-300" /> : 
                        <ChevronRight className="w-5 h-5 text-gray-300" />
                      }
                      <Icon className={`w-6 h-6 text-${category.color}-500`} />
                      <div>
                        <h4 className="font-semibold text-lg text-gray-100">{category.name}</h4>
                        <span className="text-sm text-gray-200 font-medium">
                          {subCategoryEntries.length} entries
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-xl font-bold ${
                        categoryType === EntryCategory.ASSETS || categoryType === EntryCategory.INCOME
                          ? 'text-green-500' : 'text-red-500'
                      }`}>
                        {formatCurrency(categorySubtotal)}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          onAddEntry?.(categoryType, category.name);
                        }}
                        className="text-xs"
                      >
                        + Add
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="p-4 bg-gray-800">
                    {subCategoryEntries.length > 0 ? (
                      <div className="space-y-3">
                        {subCategoryEntries.map((entry) => (
                          <div 
                            key={entry.id}
                            className="flex items-center justify-between p-3 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors"
                          >
                            <div className="flex-1">
                              <div className="font-semibold text-base" style={{color: 'white !important'}}>
                                {entry.description}
                              </div>
                              <div className="text-sm font-medium" style={{color: '#f3f4f6 !important'}}>
                                {entry.frequency !== FrequencyType.ONE_TIME && (
                                  <span className="mr-2" style={{color: '#f3f4f6 !important'}}>{entry.frequency}</span>
                                )}
                                {entry.notes && (
                                  <span className="italic" style={{color: '#f3f4f6 !important'}}>{entry.notes}</span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <div className={`text-xl font-bold ${
                                categoryType === EntryCategory.PROFILE || categoryType === EntryCategory.BENEFITS || categoryType === EntryCategory.TAX_INFO
                                  ? '!text-blue-200' 
                                  : categoryType === EntryCategory.ASSETS || categoryType === EntryCategory.INCOME
                                    ? '!text-green-200' : '!text-red-200'
                              }`}>
                                {categoryType === EntryCategory.PROFILE ? entry.notes : formatCurrency(entry.amount)}
                              </div>
                              <div className="flex items-center gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    console.log('✏️ Edit button clicked in StructuredEntrySystem');
                                    onEditEntry?.(entry);
                                  }}
                                  className="p-1"
                                >
                                  <Edit3 className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    console.log('🗑️ Delete button clicked in StructuredEntrySystem');
                                    handleDeleteEntry(entry);
                                  }}
                                  className="p-1 text-red-600 hover:text-red-700"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-6 !text-gray-100">
                        <div className="mb-2 font-medium !text-white">No {category.name.toLowerCase()} entries yet</div>
                        <div className="flex flex-wrap gap-2 justify-center">
                          {category.subcategories.slice(0, 3).map(subcat => (
                            <Button
                              key={subcat}
                              size="sm"
                              variant="outline"
                              onClick={() => onAddEntry?.(categoryType, subcat)}
                              className="text-xs"
                            >
                              + {subcat}
                            </Button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const tabs = [
    { id: EntryCategory.ASSETS, label: 'Assets', icon: '📈', color: 'green' },
    { id: EntryCategory.LIABILITIES, label: 'Liabilities', icon: '📉', color: 'red' },
    { id: EntryCategory.INCOME, label: 'Income', icon: '💰', color: 'blue' },
    { id: EntryCategory.EXPENSES, label: 'Expenses', icon: '💸', color: 'orange' },
  ];

  const getCategoriesForTab = (tab: EntryCategory) => {
    switch (tab) {
      case EntryCategory.ASSETS: return ASSET_CATEGORIES;
      case EntryCategory.LIABILITIES: return LIABILITY_CATEGORIES;
      case EntryCategory.INCOME: return INCOME_CATEGORIES;
      case EntryCategory.EXPENSES: return EXPENSE_CATEGORIES;
      default: return [];
    }
  };

  return (
    <div className="structured-entry-system">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Financial Data Entry</h1>
        <p className="text-gray-300">Organize and manage your financial information by category</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-700 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const totals = calculateTotals(tab.id);
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-200 hover:text-gray-100 hover:border-gray-500'
                }`}
              >
                <span className="text-lg">{tab.icon}</span>
                {tab.label}
                <Badge variant={activeTab === tab.id ? 'default' : 'secondary'} size="sm">
                  {totals.count}
                </Badge>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {renderCategoryPanel(getCategoriesForTab(activeTab), activeTab)}
      </div>
    </div>
  );
};

export default StructuredEntrySystem;