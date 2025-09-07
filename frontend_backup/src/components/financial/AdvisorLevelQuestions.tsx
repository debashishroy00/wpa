/**
 * WealthPath AI - Advisor Level Questions Component
 * Collects detailed financial data for personalized recommendations
 */
import React, { useState, useEffect } from 'react';
import { AlertCircle, Info, DollarSign, Percent, Calendar, Building2 } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

interface AdvisorData {
  // Mortgage Details
  mortgageRate?: number;
  mortgagePayment?: number;
  mortgageLender?: string;
  mortgageTermYears?: number;
  mortgageStartDate?: string;
  
  // Retirement Details
  contribution401k?: number;
  employerMatch?: number;
  employerMatchLimit?: number;
  vestingSchedule?: string;
  
  // Investment Details
  stockPercentage?: number;
  bondPercentage?: number;
  averageExpenseRatio?: number;
  investmentPlatform?: string;
  
  // Subscriptions
  subscriptions?: {
    name: string;
    cost: number;
    usage: 'daily' | 'weekly' | 'monthly' | 'rarely' | 'never';
  }[];
}

interface AdvisorLevelQuestionsProps {
  onSave: (data: AdvisorData) => void;
  existingData?: AdvisorData;
  category?: 'mortgage' | 'retirement' | 'investments' | 'subscriptions' | 'all';
}

const AdvisorLevelQuestions: React.FC<AdvisorLevelQuestionsProps> = ({ 
  onSave, 
  existingData = {},
  category = 'all' 
}) => {
  const [data, setData] = useState<AdvisorData>(existingData);
  const [activeSection, setActiveSection] = useState<string>('mortgage');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Common subscription services
  const commonSubscriptions = [
    { name: 'Netflix', defaultCost: 15.99, category: 'streaming' },
    { name: 'Spotify', defaultCost: 9.99, category: 'streaming' },
    { name: 'Amazon Prime', defaultCost: 14.99, category: 'shopping' },
    { name: 'Gym Membership', defaultCost: 49.99, category: 'fitness' },
    { name: 'Disney+', defaultCost: 7.99, category: 'streaming' },
    { name: 'Hulu', defaultCost: 14.99, category: 'streaming' },
    { name: 'HBO Max', defaultCost: 15.99, category: 'streaming' },
    { name: 'Apple TV+', defaultCost: 6.99, category: 'streaming' },
    { name: 'YouTube Premium', defaultCost: 11.99, category: 'streaming' },
    { name: 'Cloud Storage', defaultCost: 9.99, category: 'software' },
  ];

  const handleInputChange = (field: keyof AdvisorData, value: any) => {
    setData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleSubscriptionToggle = (subName: string, cost: number) => {
    const currentSubs = data.subscriptions || [];
    const exists = currentSubs.find(s => s.name === subName);
    
    if (exists) {
      // Remove subscription
      setData(prev => ({
        ...prev,
        subscriptions: currentSubs.filter(s => s.name !== subName)
      }));
    } else {
      // Add subscription
      setData(prev => ({
        ...prev,
        subscriptions: [...currentSubs, { name: subName, cost, usage: 'monthly' as const }]
      }));
    }
  };

  const validateAndSave = () => {
    const newErrors: Record<string, string> = {};
    
    // Validate mortgage if provided
    if (data.mortgageRate && (data.mortgageRate < 0 || data.mortgageRate > 20)) {
      newErrors.mortgageRate = 'Rate must be between 0-20%';
    }
    
    // Validate 401k
    if (data.contribution401k && (data.contribution401k < 0 || data.contribution401k > 100)) {
      newErrors.contribution401k = 'Must be between 0-100%';
    }
    
    // Validate investment allocation
    const totalAllocation = (data.stockPercentage || 0) + (data.bondPercentage || 0);
    if (totalAllocation > 0 && totalAllocation !== 100) {
      newErrors.allocation = `Stock + Bond must equal 100% (currently ${totalAllocation}%)`;
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    onSave(data);
  };

  const renderMortgageSection = () => (
    <Card className="mb-6">
      <Card.Body className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <Building2 className="w-6 h-6 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Mortgage Details</h3>
          <Badge variant="info" size="sm">Optional but Recommended</Badge>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Current Interest Rate
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.1"
                placeholder="6.5"
                value={data.mortgageRate || ''}
                onChange={(e) => handleInputChange('mortgageRate', parseFloat(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2.5 text-gray-400">%</span>
            </div>
            {errors.mortgageRate && (
              <p className="text-red-400 text-xs mt-1">{errors.mortgageRate}</p>
            )}
            <p className="text-xs text-gray-400 mt-1">Check your mortgage statement</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Monthly Payment
            </label>
            <div className="relative">
              <span className="absolute left-3 top-2.5 text-gray-400">$</span>
              <input
                type="number"
                placeholder="1890"
                value={data.mortgagePayment || ''}
                onChange={(e) => handleInputChange('mortgagePayment', parseFloat(e.target.value))}
                className="w-full pl-8 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Lender Name
            </label>
            <input
              type="text"
              placeholder="Wells Fargo"
              value={data.mortgageLender || ''}
              onChange={(e) => handleInputChange('mortgageLender', e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Loan Term
            </label>
            <select
              value={data.mortgageTermYears || ''}
              onChange={(e) => handleInputChange('mortgageTermYears', parseInt(e.target.value))}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select term</option>
              <option value="15">15 years</option>
              <option value="20">20 years</option>
              <option value="30">30 years</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Mortgage Start Date
            </label>
            <input
              type="date"
              value={data.mortgageStartDate || ''}
              onChange={(e) => handleInputChange('mortgageStartDate', e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-400 mt-1">Used to calculate payoff timeline</p>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-900/20 border border-blue-600/30 rounded-lg">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-400 mt-0.5" />
            <p className="text-sm text-blue-200">
              With this information, we can calculate potential refinancing savings and optimize your mortgage strategy.
            </p>
          </div>
        </div>
      </Card.Body>
    </Card>
  );

  const renderRetirementSection = () => (
    <Card className="mb-6">
      <Card.Body className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <DollarSign className="w-6 h-6 text-green-400" />
          <h3 className="text-lg font-semibold text-white">401(k) & Retirement</h3>
          <Badge variant="success" size="sm">High Impact</Badge>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Your Contribution Rate
            </label>
            <div className="relative">
              <input
                type="number"
                step="1"
                placeholder="6"
                value={data.contribution401k || ''}
                onChange={(e) => handleInputChange('contribution401k', parseFloat(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2.5 text-gray-400">%</span>
            </div>
            {errors.contribution401k && (
              <p className="text-red-400 text-xs mt-1">{errors.contribution401k}</p>
            )}
            <p className="text-xs text-gray-400 mt-1">Percentage of gross salary</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Employer Match
            </label>
            <div className="relative">
              <input
                type="number"
                step="1"
                placeholder="3"
                value={data.employerMatch || ''}
                onChange={(e) => handleInputChange('employerMatch', parseFloat(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2.5 text-gray-400">%</span>
            </div>
            <p className="text-xs text-gray-400 mt-1">How much employer matches</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Match Limit
            </label>
            <div className="relative">
              <input
                type="number"
                step="1"
                placeholder="6"
                value={data.employerMatchLimit || ''}
                onChange={(e) => handleInputChange('employerMatchLimit', parseFloat(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2.5 text-gray-400">%</span>
            </div>
            <p className="text-xs text-gray-400 mt-1">Up to what % they match</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Vesting Schedule
            </label>
            <select
              value={data.vestingSchedule || ''}
              onChange={(e) => handleInputChange('vestingSchedule', e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select schedule</option>
              <option value="immediate">Immediate</option>
              <option value="1-year">1 Year Cliff</option>
              <option value="3-year-graded">3 Year Graded</option>
              <option value="5-year-graded">5 Year Graded</option>
            </select>
          </div>
        </div>
        
        {data.contribution401k && data.employerMatch && data.contribution401k < (data.employerMatchLimit || data.employerMatch) && (
          <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-600/30 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5" />
              <p className="text-sm text-yellow-200">
                You're leaving free money on the table! Increase your contribution to {data.employerMatchLimit || data.employerMatch}% to get the full employer match.
              </p>
            </div>
          </div>
        )}
      </Card.Body>
    </Card>
  );

  const renderInvestmentSection = () => (
    <Card className="mb-6">
      <Card.Body className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <Percent className="w-6 h-6 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Investment Allocation</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Stock Allocation
            </label>
            <div className="relative">
              <input
                type="number"
                step="5"
                placeholder="60"
                value={data.stockPercentage || ''}
                onChange={(e) => handleInputChange('stockPercentage', parseFloat(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2.5 text-gray-400">%</span>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Bond Allocation
            </label>
            <div className="relative">
              <input
                type="number"
                step="5"
                placeholder="40"
                value={data.bondPercentage || ''}
                onChange={(e) => handleInputChange('bondPercentage', parseFloat(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2.5 text-gray-400">%</span>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Average Expense Ratio
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                placeholder="0.75"
                value={data.averageExpenseRatio || ''}
                onChange={(e) => handleInputChange('averageExpenseRatio', parseFloat(e.target.value))}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2.5 text-gray-400">%</span>
            </div>
            <p className="text-xs text-gray-400 mt-1">Average fund fees</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Investment Platform
            </label>
            <select
              value={data.investmentPlatform || ''}
              onChange={(e) => handleInputChange('investmentPlatform', e.target.value)}
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Select platform</option>
              <option value="vanguard">Vanguard</option>
              <option value="fidelity">Fidelity</option>
              <option value="schwab">Charles Schwab</option>
              <option value="etrade">E*TRADE</option>
              <option value="robinhood">Robinhood</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        
        {errors.allocation && (
          <div className="mt-4 p-3 bg-red-900/20 border border-red-600/30 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 mt-0.5" />
              <p className="text-sm text-red-200">{errors.allocation}</p>
            </div>
          </div>
        )}
      </Card.Body>
    </Card>
  );

  const renderSubscriptionsSection = () => (
    <Card className="mb-6">
      <Card.Body className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <Calendar className="w-6 h-6 text-orange-400" />
          <h3 className="text-lg font-semibold text-white">Monthly Subscriptions</h3>
          <Badge variant="warning" size="sm">
            ${((data.subscriptions || []).reduce((sum, s) => sum + s.cost, 0)).toFixed(2)}/month
          </Badge>
        </div>
        
        <p className="text-sm text-gray-300 mb-4">
          Select all subscriptions you currently have. We'll help identify ones you might not be using.
        </p>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {commonSubscriptions.map(sub => {
            const isSelected = (data.subscriptions || []).some(s => s.name === sub.name);
            return (
              <button
                key={sub.name}
                onClick={() => handleSubscriptionToggle(sub.name, sub.defaultCost)}
                className={`
                  p-3 rounded-lg border transition-all
                  ${isSelected 
                    ? 'bg-blue-900/30 border-blue-600 text-blue-300' 
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'}
                `}
              >
                <div className="font-medium text-sm">{sub.name}</div>
                <div className="text-xs mt-1">${sub.defaultCost}/mo</div>
              </button>
            );
          })}
        </div>
        
        {(data.subscriptions || []).length > 3 && (
          <div className="mt-4 p-3 bg-orange-900/20 border border-orange-600/30 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-orange-400 mt-0.5" />
              <p className="text-sm text-orange-200">
                You have {data.subscriptions?.length} subscriptions. Consider reviewing which ones you actually use regularly.
              </p>
            </div>
          </div>
        )}
      </Card.Body>
    </Card>
  );

  const shouldShowSection = (section: string) => {
    if (category === 'all') return true;
    return category === section;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-blue-600">
        <Card.Body className="p-6">
          <h2 className="text-2xl font-bold text-white mb-2">
            Advisor-Level Data Collection
          </h2>
          <p className="text-gray-300">
            Provide additional details for personalized recommendations. All fields are optional but highly recommended.
          </p>
        </Card.Body>
      </Card>

      {/* Sections */}
      {shouldShowSection('mortgage') && renderMortgageSection()}
      {shouldShowSection('retirement') && renderRetirementSection()}
      {shouldShowSection('investments') && renderInvestmentSection()}
      {shouldShowSection('subscriptions') && renderSubscriptionsSection()}

      {/* Action Buttons */}
      <div className="flex justify-end gap-3">
        <Button
          variant="outline"
          onClick={() => setData({})}
        >
          Skip for Now
        </Button>
        <Button
          variant="primary"
          onClick={validateAndSave}
        >
          Save & Generate Recommendations
        </Button>
      </div>
    </div>
  );
};

export default AdvisorLevelQuestions;