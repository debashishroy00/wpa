/**
 * WealthPath AI - Financial Management Page
 * Architecture Lead Directive: Complete structured financial data management
 */
import React, { useState } from 'react';
import { Plus, Download, Upload, RefreshCw, TrendingUp, TrendingDown, DollarSign, X, Link, Building2, Wallet, Bitcoin, CreditCard, PiggyBank, Home } from 'lucide-react';

import Button from '../ui/Button';
import Card from '../ui/Card';
import StructuredEntrySystem from './StructuredEntrySystem';
import SmartEntryModal from './SmartEntryModal';
import FinancialEntryForm from './FinancialEntryForm';
import AdvisorLevelQuestions from './AdvisorLevelQuestions';
import { FinancialEntry, EntryCategory } from '../../types/financial';
import { useCategorizedEntriesQuery } from '../../hooks/use-financial-queries';
import { useAdvisorData, useSaveAdvisorData, useSmartRecommendations } from '../../hooks/use-advisor-hooks';

const FinancialManagementPage: React.FC = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [addModalCategory, setAddModalCategory] = useState<EntryCategory | undefined>();
  const [addModalSubcategory, setAddModalSubcategory] = useState<string | undefined>();
  const [editingEntry, setEditingEntry] = useState<FinancialEntry | null>(null);
  const [showAdvisorQuestions, setShowAdvisorQuestions] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'advisor' | 'connections'>('overview');

  const { data: categorizedData, isLoading, refetch } = useCategorizedEntriesQuery();
  const { data: advisorData } = useAdvisorData();
  const saveAdvisorData = useSaveAdvisorData();
  const { data: smartRecommendations } = useSmartRecommendations();

  // Debug logging to see what data we're getting
  console.log('🔍 Categorized Data:', categorizedData);

  // Extract data from the new backend response structure
  const summary = categorizedData?.summary || {
    net_worth: 0,
    monthly_income: 0,
    monthly_expenses: 0,
    monthly_cash_flow: 0,
    total_assets: 0,
    total_liabilities: 0,
    savings_rate: 0
  };

  // Extract calculated totals from summary
  const totalAssets = summary.total_assets;
  const totalLiabilities = summary.total_liabilities;
  const monthlyIncome = summary.monthly_income;
  const monthlyExpenses = summary.monthly_expenses;
  const netWorth = summary.net_worth;
  const monthlyCashFlow = summary.monthly_cash_flow;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleAddEntry = (category?: EntryCategory, subcategory?: string) => {
    setAddModalCategory(category);
    setAddModalSubcategory(subcategory);
    setIsAddModalOpen(true);
  };

  const handleEditEntry = (entry: FinancialEntry) => {
    console.log('✏️ Edit button clicked for entry:', entry);
    console.log('✏️ Entry ID:', entry.id, 'Type:', typeof entry.id);
    
    // Check if this is a profile entry (synthetic ID starting with 'profile-')
    if (typeof entry.id === 'string' && entry.id.startsWith('profile-')) {
      console.log('✏️ Opening profile edit for:', entry);
      // Open the add modal in profile mode for editing this specific field
      setAddModalCategory(EntryCategory.PROFILE);
      setAddModalSubcategory('Personal Information'); // Default to personal info
      setEditingEntry(entry); // Pass the profile entry to edit
      setIsAddModalOpen(true);
      return;
    }
    
    // Check if this is a family entry (synthetic ID starting with 'family-')
    if (typeof entry.id === 'string' && entry.id.startsWith('family-')) {
      console.warn('🚫 EDIT BLOCKED: Family entries cannot be edited from this view.');
      setTimeout(() => {
        alert('Family entries cannot be edited from this view.\n\nPlease use the Profile tab to manage family information.');
      }, 100);
      return;
    }
    
    // Check if this is a benefit or tax entry (synthetic IDs)
    if (typeof entry.id === 'string' && (entry.id.startsWith('benefit-') || entry.id.startsWith('tax-'))) {
      console.warn('🚫 EDIT BLOCKED: Benefit and tax entries cannot be edited from this view.');
      setTimeout(() => {
        alert('Benefit and tax entries cannot be edited from this view.\n\nPlease use the respective tabs to manage this information.');
      }, 100);
      return;
    }
    
    setEditingEntry(entry);
  };

  const handleModalSuccess = () => {
    refetch(); // Refresh data
    // Close modal immediately after success
    setIsAddModalOpen(false);
    setEditingEntry(null);
  };

  const handleAdvisorDataSave = async (data: any) => {
    try {
      await saveAdvisorData.mutateAsync(data);
      setShowAdvisorQuestions(false);
      // Refresh data
      refetch();
    } catch (error) {
      console.error('Failed to save advisor data:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <DollarSign className="w-8 h-8 text-green-500" />
                Financial Management
              </h1>
              <p className="text-gray-300 mt-1">Complete financial overview, advisor-level insights, and intelligent data management</p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => refetch()}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                onClick={() => handleAddEntry()}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Add Entry
              </Button>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="border-b border-gray-700">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'overview', label: 'Overview', icon: DollarSign },
                { id: 'advisor', label: 'Advisor Data', icon: TrendingUp },
                { id: 'connections', label: 'Account Connections', icon: Link }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`
                    flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-300'
                      : 'border-transparent text-gray-500 hover:text-gray-300 hover:border-gray-300'
                    }
                  `}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                  {tab.id === 'advisor' && smartRecommendations && smartRecommendations.length > 0 && (
                    <span className="bg-red-500 text-white text-xs rounded-full px-2 py-0.5">
                      {smartRecommendations.length}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary Dashboard */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="bg-gradient-to-r from-blue-900 to-blue-800">
                <Card.Body className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-200 text-sm">Net Worth</p>
                      <p className="text-2xl font-bold text-white">{formatCurrency(netWorth)}</p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-blue-400" />
                  </div>
                  <div className="mt-2 text-xs text-blue-300">
                    <p>Assets: {formatCurrency(totalAssets)}</p>
                    <p>Liabilities: {formatCurrency(totalLiabilities)}</p>
                  </div>
                </Card.Body>
              </Card>

              <Card className="bg-gradient-to-r from-green-900 to-green-800">
                <Card.Body className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-200 text-sm">Monthly Income</p>
                      <p className="text-2xl font-bold text-white">{formatCurrency(monthlyIncome)}</p>
                    </div>
                    <DollarSign className="w-8 h-8 text-green-400" />
                  </div>
                  <div className="mt-2">
                    <p className="text-xs text-green-300">
                      Annual: {formatCurrency(monthlyIncome * 12)}
                    </p>
                  </div>
                </Card.Body>
              </Card>

              <Card className="bg-gradient-to-r from-red-900 to-red-800">
                <Card.Body className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-red-200 text-sm">Monthly Expenses</p>
                      <p className="text-2xl font-bold text-white">{formatCurrency(monthlyExpenses)}</p>
                    </div>
                    <TrendingDown className="w-8 h-8 text-red-400" />
                  </div>
                  <div className="mt-2">
                    <p className="text-xs text-red-300">
                      Annual: {formatCurrency(monthlyExpenses * 12)}
                    </p>
                  </div>
                </Card.Body>
              </Card>

              <Card className={`bg-gradient-to-r ${
                monthlyCashFlow >= 0 
                  ? 'from-purple-900 to-purple-800' 
                  : 'from-orange-900 to-orange-800'
              }`}>
                <Card.Body className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`text-sm ${monthlyCashFlow >= 0 ? 'text-purple-200' : 'text-orange-200'}`}>Monthly Cash Flow</p>
                      <p className="text-2xl font-bold text-white">
                        {formatCurrency(monthlyCashFlow)}
                      </p>
                    </div>
                    {monthlyCashFlow >= 0 ? (
                      <TrendingUp className="w-8 h-8 text-purple-400" />
                    ) : (
                      <TrendingDown className="w-8 h-8 text-orange-400" />
                    )}
                  </div>
                  <div className="mt-2">
                    <p className={`text-xs ${monthlyCashFlow >= 0 ? 'text-purple-300' : 'text-orange-300'}`}>
                      Savings Rate: {monthlyIncome > 0 ? ((monthlyCashFlow / monthlyIncome) * 100).toFixed(1) : 0}%
                    </p>
                  </div>
                </Card.Body>
              </Card>
            </div>

            {/* Main Content - Structured Entry System */}
            <Card className="hover:border-blue-600 transition-colors">
              <StructuredEntrySystem
                onAddEntry={handleAddEntry}
                onEditEntry={handleEditEntry}
              />
            </Card>
          </div>
        )}

        {/* Advisor Data Tab */}
        {activeTab === 'advisor' && (
          <div className="space-y-6">
            {showAdvisorQuestions ? (
              <AdvisorLevelQuestions
                onSave={handleAdvisorDataSave}
                existingData={advisorData}
              />
            ) : (
              <>
                {/* Smart Recommendations Section */}
                {smartRecommendations && smartRecommendations.length > 0 && (
                  <Card className="bg-gradient-to-r from-green-900/20 to-blue-900/20 border-green-600">
                    <Card.Body className="p-6">
                      <h3 className="text-xl font-semibold text-green-100 mb-4">
                        🎯 Smart Recommendations ({smartRecommendations.length})
                      </h3>
                      <div className="space-y-4">
                        {smartRecommendations.slice(0, 3).map(rec => (
                          <div key={rec.id} className="border border-green-600/30 rounded-lg p-4 bg-green-900/10">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-medium text-white">{rec.title}</h4>
                              <span className={`text-xs px-2 py-1 rounded ${
                                rec.difficulty === 'easy' ? 'bg-green-600 text-white' :
                                rec.difficulty === 'medium' ? 'bg-yellow-600 text-white' :
                                'bg-red-600 text-white'
                              }`}>
                                {rec.difficulty}
                              </span>
                            </div>
                            <p className="text-green-200 text-sm mb-3">{rec.description}</p>
                            {rec.monthlySavings && (
                              <div className="flex items-center gap-4 text-sm">
                                <span className="text-green-400 font-semibold">
                                  Save ${rec.monthlySavings}/month
                                </span>
                                <span className="text-green-300">
                                  ${rec.annualSavings}/year
                                </span>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </Card.Body>
                  </Card>
                )}

                {/* Enhanced Data Collection Prompt */}
                <Card className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-blue-600">
                  <Card.Body className="p-6">
                    <div className="text-center">
                      <h3 className="text-2xl font-bold text-white mb-4">
                        Get Advisor-Level Recommendations
                      </h3>
                      <p className="text-gray-300 mb-6">
                        Answer a few quick questions about your mortgage, 401k, and subscriptions to unlock personalized financial recommendations.
                      </p>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="text-center">
                          <div className="text-2xl mb-2">🏠</div>
                          <div className="text-sm text-gray-300">Mortgage Rate</div>
                          <div className="text-xs text-blue-400">
                            {advisorData?.mortgageRate ? `${advisorData.mortgageRate}%` : 'Not provided'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl mb-2">💰</div>
                          <div className="text-sm text-gray-300">401k Contribution</div>
                          <div className="text-xs text-blue-400">
                            {advisorData?.contribution401k ? `${advisorData.contribution401k}%` : 'Not provided'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl mb-2">📊</div>
                          <div className="text-sm text-gray-300">Stock Allocation</div>
                          <div className="text-xs text-blue-400">
                            {advisorData?.stockPercentage ? `${advisorData.stockPercentage}%` : 'Not provided'}
                          </div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl mb-2">📱</div>
                          <div className="text-sm text-gray-300">Subscriptions</div>
                          <div className="text-xs text-blue-400">
                            {advisorData?.subscriptions?.length || 0} tracked
                          </div>
                        </div>
                      </div>

                      <Button
                        onClick={() => setShowAdvisorQuestions(true)}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        {Object.keys(advisorData || {}).length > 0 ? 'Update' : 'Add'} Advisor Data
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              </>
            )}
          </div>
        )}

        {/* Account Connections Tab */}
        {activeTab === 'connections' && (
          <div className="space-y-6">
            {/* Connection Status Overview */}
            <Card className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-blue-600">
              <Card.Body className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-white">Account Connections</h3>
                    <p className="text-gray-300 mt-1">Connect your accounts for automatic data sync and real-time insights</p>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-blue-400">0</div>
                    <div className="text-sm text-gray-300">Connected Accounts</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-gray-800 rounded-lg">
                    <div className="text-2xl mb-2">🏦</div>
                    <div className="text-sm text-gray-300">Banking</div>
                    <div className="text-xs text-red-400">Not Connected</div>
                  </div>
                  <div className="text-center p-4 bg-gray-800 rounded-lg">
                    <div className="text-2xl mb-2">📈</div>
                    <div className="text-sm text-gray-300">Investments</div>
                    <div className="text-xs text-red-400">Not Connected</div>
                  </div>
                  <div className="text-center p-4 bg-gray-800 rounded-lg">
                    <div className="text-2xl mb-2">🏠</div>
                    <div className="text-sm text-gray-300">Real Estate</div>
                    <div className="text-xs text-red-400">Not Connected</div>
                  </div>
                  <div className="text-center p-4 bg-gray-800 rounded-lg">
                    <div className="text-2xl mb-2">₿</div>
                    <div className="text-sm text-gray-300">Crypto</div>
                    <div className="text-xs text-red-400">Not Connected</div>
                  </div>
                </div>
              </Card.Body>
            </Card>

            {/* Banking Connections */}
            <Card className="bg-gray-800 border-gray-700">
              <Card.Body className="p-6">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <Building2 className="w-6 h-6 text-blue-400" />
                  Banking & Credit Cards
                </h3>
                <p className="text-gray-300 mb-6">Connect your bank accounts, credit cards, and loan accounts through Plaid's secure connection.</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {['Chase', 'Bank of America', 'Wells Fargo', 'Citi', 'Capital One', 'American Express'].map(bank => (
                    <Button
                      key={bank}
                      variant="outline"
                      className="flex items-center justify-between p-4 h-auto"
                    >
                      <div className="flex items-center gap-3">
                        <CreditCard className="w-6 h-6 text-blue-400" />
                        <span>{bank}</span>
                      </div>
                      <span className="text-xs text-gray-400">Connect</span>
                    </Button>
                  ))}
                </div>
                
                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  <Link className="w-4 h-4 mr-2" />
                  Connect Banking Accounts via Plaid
                </Button>
              </Card.Body>
            </Card>

            {/* Investment Connections */}
            <Card className="bg-gray-800 border-gray-700">
              <Card.Body className="p-6">
                <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-6 h-6 text-green-400" />
                  Investment & Retirement Accounts
                </h3>
                <p className="text-gray-300 mb-6">Connect your brokerage, 401k, IRA, and other investment accounts.</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {['Fidelity', 'Charles Schwab', 'Vanguard', 'E*TRADE', 'TD Ameritrade', 'Robinhood'].map(broker => (
                    <Button
                      key={broker}
                      variant="outline"
                      className="flex items-center justify-between p-4 h-auto"
                    >
                      <div className="flex items-center gap-3">
                        <PiggyBank className="w-6 h-6 text-green-400" />
                        <span>{broker}</span>
                      </div>
                      <span className="text-xs text-gray-400">Connect</span>
                    </Button>
                  ))}
                </div>
                
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  <Link className="w-4 h-4 mr-2" />
                  Connect Investment Accounts
                </Button>
              </Card.Body>
            </Card>

            {/* Real Estate & Alternative Assets */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="bg-gray-800 border-gray-700">
                <Card.Body className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Home className="w-6 h-6 text-purple-400" />
                    Real Estate
                  </h3>
                  <p className="text-gray-300 mb-4 text-sm">Connect your mortgage and track property values.</p>
                  
                  <div className="space-y-3 mb-4">
                    <Button
                      variant="outline"
                      className="w-full flex items-center justify-between"
                    >
                      <span>Zillow Integration</span>
                      <span className="text-xs text-gray-400">Property Values</span>
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full flex items-center justify-between"
                    >
                      <span>Mortgage Lender</span>
                      <span className="text-xs text-gray-400">Loan Details</span>
                    </Button>
                  </div>
                  
                  <Button className="w-full bg-purple-600 hover:bg-purple-700 text-sm">
                    Connect Real Estate
                  </Button>
                </Card.Body>
              </Card>

              <Card className="bg-gray-800 border-gray-700">
                <Card.Body className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Bitcoin className="w-6 h-6 text-orange-400" />
                    Cryptocurrency
                  </h3>
                  <p className="text-gray-300 mb-4 text-sm">Connect crypto exchanges and wallets.</p>
                  
                  <div className="space-y-3 mb-4">
                    <Button
                      variant="outline"
                      className="w-full flex items-center justify-between"
                    >
                      <span>Coinbase</span>
                      <span className="text-xs text-gray-400">Exchange</span>
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full flex items-center justify-between"
                    >
                      <span>Binance</span>
                      <span className="text-xs text-gray-400">Exchange</span>
                    </Button>
                  </div>
                  
                  <Button className="w-full bg-orange-600 hover:bg-orange-700 text-sm">
                    Connect Crypto Accounts
                  </Button>
                </Card.Body>
              </Card>
            </div>

            {/* Manual Entry Fallback */}
            <Card className="bg-gradient-to-r from-gray-800 to-gray-700 border-gray-600">
              <Card.Body className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Manual Entry</h3>
                <p className="text-gray-300 mb-4">Can't find your account? Add entries manually and upgrade later.</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Button
                    onClick={() => {
                      setActiveTab('overview');
                      setTimeout(() => handleAddEntry('income', 'salary'), 100);
                    }}
                    variant="outline"
                    className="flex flex-col items-center gap-2 py-4"
                  >
                    <DollarSign className="w-6 h-6 text-green-400" />
                    <span>Add Income</span>
                  </Button>
                  <Button
                    onClick={() => {
                      setActiveTab('overview');
                      setTimeout(() => handleAddEntry('assets', 'investment'), 100);
                    }}
                    variant="outline"
                    className="flex flex-col items-center gap-2 py-4"
                  >
                    <TrendingUp className="w-6 h-6 text-blue-400" />
                    <span>Add Asset</span>
                  </Button>
                  <Button
                    onClick={() => {
                      setActiveTab('overview');
                      setTimeout(() => handleAddEntry('expenses', 'housing'), 100);
                    }}
                    variant="outline"
                    className="flex flex-col items-center gap-2 py-4"
                  >
                    <Home className="w-6 h-6 text-purple-400" />
                    <span>Add Expense</span>
                  </Button>
                  <Button
                    onClick={() => {
                      setActiveTab('overview');
                      setTimeout(() => handleAddEntry('liabilities', 'credit_card'), 100);
                    }}
                    variant="outline"
                    className="flex flex-col items-center gap-2 py-4"
                  >
                    <CreditCard className="w-6 h-6 text-red-400" />
                    <span>Add Debt</span>
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </div>
        )}

        {/* Modals */}
        <SmartEntryModal
          isOpen={isAddModalOpen}
          onClose={() => {
            setIsAddModalOpen(false);
            setAddModalCategory(undefined);
            setAddModalSubcategory(undefined);
            setEditingEntry(null); // Clear editing entry when closing
          }}
          category={addModalCategory}
          subcategory={addModalSubcategory}
          onSuccess={handleModalSuccess}
          editingEntry={editingEntry} // Pass editing entry for profile editing
        />

        {/* Edit Modal - Only for financial entries, not profile entries */}
        {editingEntry && !(typeof editingEntry.id === 'string' && editingEntry.id.startsWith('profile-')) && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto border border-gray-700">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold text-white">Edit Entry</h2>
                  <button
                    onClick={() => setEditingEntry(null)}
                    className="text-gray-400 hover:text-white"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>
                <FinancialEntryForm
                  entry={editingEntry}
                  onSuccess={handleModalSuccess}
                  onCancel={() => setEditingEntry(null)}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialManagementPage;