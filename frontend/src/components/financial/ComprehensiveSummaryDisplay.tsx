/**
 * WealthPath AI - Comprehensive Summary Display Component
 * Shows complete financial profile data with ALL user preferences
 */
import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  User,
  Settings,
  Target,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Eye,
  EyeOff,
  Shield,
  Database
} from 'lucide-react';

import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import ComprehensiveSummaryService from '../../services/ComprehensiveSummaryService';
import VectorDBService, { VectorStatus } from '../../services/VectorDBService';
import { ComprehensiveSummary } from '../../types/financial.types';
import { useUnifiedAuthStore } from '../../stores/unified-auth-store';

const ComprehensiveSummaryDisplay: React.FC = () => {
  const user = useUnifiedAuthStore((state) => state.user);
  const [summary, setSummary] = useState<ComprehensiveSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFullJson, setShowFullJson] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    preferences: true,
    financial: true,
    goals: true,
    recommendations: true
  });

  // Vector database states
  const [indexing, setIndexing] = useState(false);
  const [vectorStatus, setVectorStatus] = useState<VectorStatus | null>(null);
  const [indexingMessage, setIndexingMessage] = useState<string>('');

  const service = ComprehensiveSummaryService.getInstance();

  useEffect(() => {
    if (user?.id) {
      loadSummary();
      loadVectorStatus();
    }
  }, [user?.id]);

  const loadSummary = async () => {
    if (!user?.id) {
      setError('User not authenticated');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await service.getComprehensiveSummary(user.id);
      setSummary(data);
    } catch (error) {
      console.error('Failed to load comprehensive summary:', error);
      setError(error instanceof Error ? error.message : 'Failed to load summary');
    } finally {
      setLoading(false);
    }
  };

  const loadVectorStatus = async () => {
    if (!user?.id) return;

    try {
      const status = await VectorDBService.getVectorStatus(user.id);
      setVectorStatus(status);
    } catch (error) {
      console.error('Failed to load vector status:', error);
      // Don't show error for this, as it's supplementary info
    }
  };

  const handleIndexData = async () => {
    if (!user?.id) return;

    try {
      setIndexing(true);
      setIndexingMessage('Preparing financial data...');
      
      const result = await VectorDBService.indexUserData(user.id);
      
      setIndexingMessage(`Successfully indexed ${result.documents_indexed} documents`);
      
      // Refresh vector status
      await loadVectorStatus();
      
      // Show success message briefly
      setTimeout(() => {
        setIndexingMessage('');
      }, 3000);
      
    } catch (error) {
      console.error('Failed to index data:', error);
      setIndexingMessage(`Failed to index data: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
      // Clear error message after 5 seconds
      setTimeout(() => {
        setIndexingMessage('');
      }, 5000);
    } finally {
      setIndexing(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-700 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <Card.Body className="text-center py-8">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Summary</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={loadSummary} leftIcon={<RefreshCw className="w-4 h-4" />}>
            Retry
          </Button>
        </Card.Body>
      </Card>
    );
  }

  if (!summary) {
    return (
      <Card>
        <Card.Body className="text-center py-8">
          <p className="text-gray-600">No comprehensive summary available</p>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-white">Financial Profile Data</h2>
          <p className="text-sm text-gray-300 mt-1">
            Complete financial summary with preferences • Data Quality: {summary.database_metadata.data_quality_score}/100
            {vectorStatus && (
              <span className="ml-2">
                • Vector DB: {vectorStatus.is_indexed ? 
                  `${vectorStatus.total_documents} docs indexed` : 
                  'Not indexed'
                }
              </span>
            )}
          </p>
          {indexingMessage && (
            <p className={`text-sm mt-1 ${indexingMessage.includes('Successfully') ? 'text-green-400' : 'text-yellow-400'}`}>
              {indexingMessage}
            </p>
          )}
        </div>
        <div className="flex space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleIndexData}
            disabled={indexing}
            leftIcon={<Database className={`w-4 h-4 ${indexing ? 'animate-pulse' : ''}`} />}
            className={`${vectorStatus?.is_indexed ? 'border-green-500 text-green-400' : 'border-blue-500 text-blue-400'}`}
          >
            {indexing ? 'Indexing...' : (vectorStatus?.is_indexed ? 'Reindex' : 'Index to Vector DB')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={loadSummary}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFullJson(!showFullJson)}
            leftIcon={showFullJson ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          >
            {showFullJson ? 'Hide' : 'View'} Full Profile JSON
          </Button>
        </div>
      </div>

      {/* Key Financial Metrics - Similar to S1.png */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gray-800 border-gray-600">
          <Card.Body className="p-4">
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="w-5 h-5 text-blue-400" />
              <Badge variant="info" size="sm" className="bg-blue-600 text-white">Net Worth</Badge>
            </div>
            <h3 className="text-sm font-medium text-gray-300">Net Worth</h3>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(summary.financials.netWorth)}
            </p>
          </Card.Body>
        </Card>

        <Card className="bg-gray-800 border-gray-600">
          <Card.Body className="p-4">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              <Badge variant="success" size="sm" className="bg-green-600 text-white">Income</Badge>
            </div>
            <h3 className="text-sm font-medium text-gray-300">Monthly Income</h3>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(summary.financials.monthlyIncome)}
            </p>
          </Card.Body>
        </Card>

        <Card className="bg-gray-800 border-gray-600">
          <Card.Body className="p-4">
            <div className="flex items-center justify-between mb-2">
              <TrendingDown className="w-5 h-5 text-red-400" />
              <Badge variant="warning" size="sm" className="bg-red-600 text-white">Expenses</Badge>
            </div>
            <h3 className="text-sm font-medium text-gray-300">Monthly Expenses</h3>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(summary.financials.monthlyExpenses)}
            </p>
          </Card.Body>
        </Card>

        <Card className="bg-gray-800 border-gray-600">
          <Card.Body className="p-4">
            <div className="flex items-center justify-between mb-2">
              <DollarSign className="w-5 h-5 text-purple-400" />
              <Badge variant="info" size="sm" className="bg-purple-600 text-white">Surplus</Badge>
            </div>
            <h3 className="text-sm font-medium text-gray-300">Monthly Surplus</h3>
            <p className="text-2xl font-bold text-white">
              {formatCurrency(summary.financials.monthlySurplus)}
            </p>
          </Card.Body>
        </Card>
      </div>

      {/* User Preferences Section */}
      <Card className="bg-gray-800 border-gray-600">
        <Card.Header>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Settings className="w-5 h-5 text-blue-400" />
              <Card.Title className="text-white">Financial Preferences Profile</Card.Title>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleSection('preferences')}
              rightIcon={expandedSections.preferences ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
              className="text-gray-300 hover:text-white"
            >
              {expandedSections.preferences ? 'Collapse' : 'Expand'}
            </Button>
          </div>
        </Card.Header>
        {expandedSections.preferences && (
          <Card.Body>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Basic Preferences */}
              <div>
                <h4 className="font-semibold text-white mb-3 flex items-center">
                  <User className="w-4 h-4 mr-2 text-blue-400" />
                  Basic Preferences
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Risk Tolerance:</span>
                    <span className="font-medium text-white">{summary.preferences.risk_tolerance}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Risk Score:</span>
                    <span className="font-medium text-white">{summary.preferences.risk_score || 'N/A'}/10</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Investment Timeline:</span>
                    <span className="font-medium text-white">{summary.preferences.investment_timeline} years</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Financial Knowledge:</span>
                    <span className="font-medium text-white">{summary.preferences.financial_knowledge}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Emergency Fund Target:</span>
                    <span className="font-medium text-white">{summary.preferences.emergency_fund_months} months</span>
                  </div>
                </div>
              </div>

              {/* Investment Preferences */}
              <div>
                <h4 className="font-semibold text-white mb-3 flex items-center">
                  <TrendingUp className="w-4 h-4 mr-2 text-green-400" />
                  Investment Style
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Investment Style:</span>
                    <span className="font-medium text-white">{summary.preferences.investment_style || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Stocks Preference:</span>
                    <span className="font-medium text-white">{summary.preferences.stocks_preference || 'N/A'}/10</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Bonds Preference:</span>
                    <span className="font-medium text-white">{summary.preferences.bonds_preference || 'N/A'}/10</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Real Estate:</span>
                    <span className="font-medium text-white">{summary.preferences.real_estate_preference || 'N/A'}/10</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Crypto Preference:</span>
                    <span className="font-medium text-white">{summary.preferences.crypto_preference || 'N/A'}/10</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">ESG Investing:</span>
                    <span className="font-medium text-white">{summary.preferences.esg_investing ? 'Yes' : 'No'}</span>
                  </div>
                </div>
              </div>

              {/* Tax & Retirement */}
              <div>
                <h4 className="font-semibold text-white mb-3 flex items-center">
                  <DollarSign className="w-4 h-4 mr-2 text-yellow-400" />
                  Tax & Retirement
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Filing Status:</span>
                    <span className="font-medium text-white">{summary.preferences.tax_filing_status || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Federal Tax Bracket:</span>
                    <span className="font-medium text-white">
                      {summary.preferences.federal_tax_bracket ? formatPercentage(summary.preferences.federal_tax_bracket) : 'Not specified'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">State:</span>
                    <span className="font-medium text-white">{summary.preferences.state || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Tax Loss Harvesting:</span>
                    <span className="font-medium text-white">{summary.preferences.tax_loss_harvesting ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Retirement Lifestyle:</span>
                    <span className="font-medium text-white">{summary.preferences.retirement_lifestyle || 'Not specified'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Work Flexibility:</span>
                    <span className="font-medium text-white">
                      {summary.preferences.work_flexibility?.part_time ? 'Part-time OK' : ''} 
                      {summary.preferences.work_flexibility?.consulting ? ', Consulting OK' : ''}
                      {!summary.preferences.work_flexibility?.part_time && !summary.preferences.work_flexibility?.consulting ? 'Not specified' : ''}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </Card.Body>
        )}
      </Card>

      {/* Financial Details */}
      <Card className="bg-gray-800 border-gray-600">
        <Card.Header>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <DollarSign className="w-5 h-5 text-green-400" />
              <Card.Title className="text-white">Financial Details</Card.Title>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleSection('financial')}
              rightIcon={expandedSections.financial ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
              className="text-gray-300 hover:text-white"
            >
              {expandedSections.financial ? 'Collapse' : 'Expand'}
            </Button>
          </div>
        </Card.Header>
        {expandedSections.financial && (
          <Card.Body>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-white mb-3 flex items-center">
                  <Target className="w-4 h-4 mr-2 text-blue-400" />
                  Asset Allocation
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">Real Estate:</span>
                    <div className="text-right">
                      <span className="font-medium text-white">{summary.financials.assetAllocation.realEstate.percentage}%</span>
                      <div className="text-sm text-gray-400">
                        {formatCurrency(summary.financials.assetAllocation.realEstate.value)}
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">Investments:</span>
                    <div className="text-right">
                      <span className="font-medium text-white">{summary.financials.assetAllocation.investments.percentage}%</span>
                      <div className="text-sm text-gray-400">
                        {formatCurrency(summary.financials.assetAllocation.investments.value)}
                      </div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300">Cash:</span>
                    <div className="text-right">
                      <span className="font-medium text-white">{summary.financials.assetAllocation.cash.percentage}%</span>
                      <div className="text-sm text-gray-400">
                        {formatCurrency(summary.financials.assetAllocation.cash.value)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-white mb-3 flex items-center">
                  <TrendingUp className="w-4 h-4 mr-2 text-green-400" />
                  Key Ratios
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Savings Rate:</span>
                    <span className="font-medium text-green-400">{summary.financials.savingsRate}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Debt-to-Income:</span>
                    <span className="font-medium text-white">{summary.financials.debtToIncomeRatio}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Emergency Fund:</span>
                    <span className="font-medium text-white">{summary.financials.emergencyFundCoverage} months</span>
                  </div>
                </div>
              </div>
            </div>
          </Card.Body>
        )}
      </Card>

      {/* Goals */}
      {summary.goals && summary.goals.length > 0 && (
        <Card className="bg-gray-800 border-gray-600">
          <Card.Header>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Target className="w-5 h-5 text-purple-400" />
                <Card.Title className="text-white">Financial Goals</Card.Title>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleSection('goals')}
                rightIcon={expandedSections.goals ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
                className="text-gray-300 hover:text-white"
              >
                {expandedSections.goals ? 'Collapse' : 'Expand'}
              </Button>
            </div>
          </Card.Header>
          {expandedSections.goals && (
            <Card.Body>
              <div className="space-y-4">
                {summary.goals.map((goal, index) => (
                  <div key={goal.goal_id} className="border border-gray-600 rounded-lg p-4 bg-gray-700">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-white">{goal.name}</h4>
                      <Badge variant="info" className="bg-purple-600 text-white">{goal.category}</Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-300">Target:</span>
                        <div className="font-medium text-white">{formatCurrency(goal.target_amount)}</div>
                      </div>
                      <div>
                        <span className="text-gray-300">Progress:</span>
                        <div className="font-medium text-green-400">{goal.progressPercentage}%</div>
                      </div>
                      <div>
                        <span className="text-gray-300">Monthly Required:</span>
                        <div className="font-medium text-white">{formatCurrency(goal.monthlyRequired)}</div>
                      </div>
                      <div>
                        <span className="text-gray-300">Target Date:</span>
                        <div className="font-medium text-white">{goal.target_date}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card.Body>
          )}
        </Card>
      )}

      {/* Recommendations */}
      <Card className="bg-gray-800 border-gray-600">
        <Card.Header>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-blue-400" />
              <Card.Title className="text-white">Personalized Recommendations</Card.Title>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleSection('recommendations')}
              rightIcon={expandedSections.recommendations ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
              className="text-gray-300 hover:text-white"
            >
              {expandedSections.recommendations ? 'Collapse' : 'Expand'}
            </Button>
          </div>
        </Card.Header>
        {expandedSections.recommendations && (
          <Card.Body>
            <div className="space-y-4">
              {summary.recommendations.portfolio_adjustment && (
                <div>
                  <h4 className="font-semibold text-white mb-2 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-2 text-green-400" />
                    Portfolio Adjustment
                  </h4>
                  <p className="text-gray-300">{summary.recommendations.portfolio_adjustment}</p>
                </div>
              )}
              
              {summary.recommendations.risk_assessment && (
                <div>
                  <h4 className="font-semibold text-white mb-2 flex items-center">
                    <Shield className="w-4 h-4 mr-2 text-blue-400" />
                    Risk Assessment
                  </h4>
                  <p className="text-gray-300">{summary.recommendations.risk_assessment}</p>
                </div>
              )}

              {summary.recommendations.tax_optimization && (
                <div>
                  <h4 className="font-semibold text-white mb-2 flex items-center">
                    <DollarSign className="w-4 h-4 mr-2 text-yellow-400" />
                    Tax Optimization
                  </h4>
                  <p className="text-gray-300">{summary.recommendations.tax_optimization}</p>
                </div>
              )}

              {summary.recommendations.next_steps && summary.recommendations.next_steps.length > 0 && (
                <div>
                  <h4 className="font-semibold text-white mb-2 flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                    Next Steps
                  </h4>
                  <ul className="list-disc list-inside space-y-1">
                    {summary.recommendations.next_steps.map((step, index) => (
                      <li key={index} className="text-gray-300">{step}</li>
                    ))}
                  </ul>
                </div>
              )}

              {summary.recommendations.warnings && summary.recommendations.warnings.length > 0 && (
                <div>
                  <h4 className="font-semibold text-white mb-2 flex items-center">
                    <AlertTriangle className="w-4 h-4 mr-2 text-yellow-400" />
                    Warnings
                  </h4>
                  <ul className="list-disc list-inside space-y-1">
                    {summary.recommendations.warnings.map((warning, index) => (
                      <li key={index} className="text-yellow-300">{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card.Body>
        )}
      </Card>

      {/* Full JSON View - Similar to S1.png dropdown */}
      {showFullJson && (
        <Card className="bg-gray-800 border-gray-600">
          <Card.Header>
            <Card.Title className="text-white">▼ View Full Profile JSON</Card.Title>
          </Card.Header>
          <Card.Body>
            <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto max-h-96 font-mono border border-gray-700">
              {JSON.stringify(summary, null, 2)}
            </pre>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default ComprehensiveSummaryDisplay;