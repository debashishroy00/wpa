import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  DollarSign, 
  TrendingUp, 
  Calculator, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  RefreshCw,
  Target,
  Info
} from 'lucide-react';

interface TaxInsight {
  strategy: string;
  potentialSavings: number;
  difficulty: 'Easy' | 'Medium' | 'Complex';
  timeline: string;
  priority: number;
  description: string;
  implementationSteps?: string[];
}

interface TaxProfile {
  annual_income: number;
  tax_bracket: number;
  filing_status: string;
}

interface TaxInsightsResponse {
  insights: TaxInsight[];
  total_potential_savings: number;
  tax_profile: TaxProfile;
  generated_at: string;
}

const TaxInsights: React.FC = () => {
  const [insights, setInsights] = useState<TaxInsight[]>([]);
  const [totalSavings, setTotalSavings] = useState<number>(0);
  const [taxProfile, setTaxProfile] = useState<TaxProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [expandedInsight, setExpandedInsight] = useState<number | null>(null);

  const fetchTaxInsights = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch('/api/v1/tax/insights', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: TaxInsightsResponse = await response.json();
      
      setInsights(data.insights || []);
      setTotalSavings(data.total_potential_savings || 0);
      setTaxProfile(data.tax_profile || null);
      setLastUpdated(new Date(data.generated_at || Date.now()).toLocaleString());
      
    } catch (err) {
      console.error('Failed to fetch tax insights:', err);
      setError(err instanceof Error ? err.message : 'Failed to load tax insights');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTaxInsights();
  }, []);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Complex':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getDifficultyIcon = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'Medium':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      case 'Complex':
        return <AlertCircle className="w-4 h-4 text-red-600" />;
      default:
        return <Info className="w-4 h-4 text-gray-600" />;
    }
  };

  const getPriorityBadge = (priority: number) => {
    if (priority <= 1) {
      return <Badge className="bg-red-100 text-red-800 border-red-200">High Priority</Badge>;
    } else if (priority <= 2) {
      return <Badge className="bg-orange-100 text-orange-800 border-orange-200">Medium Priority</Badge>;
    } else {
      return <Badge className="bg-blue-100 text-blue-800 border-blue-200">Low Priority</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="bg-gray-800 border-gray-700">
          <CardContent className="p-6">
            <div className="flex items-center justify-center space-x-3">
              <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
              <span className="text-gray-300">Analyzing your tax optimization opportunities...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="bg-gray-800 border-gray-700">
        <CardContent className="p-6">
          <div className="flex items-center space-x-3 text-red-400 mb-4">
            <AlertCircle className="w-5 h-5" />
            <span>Error loading tax insights</span>
          </div>
          <p className="text-gray-400 mb-4">{error}</p>
          <Button 
            onClick={fetchTaxInsights}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (insights.length === 0) {
    return (
      <Card className="bg-gray-800 border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-100 flex items-center space-x-2">
            <Calculator className="w-5 h-5 text-blue-400" />
            <span>Tax Optimization</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="text-center py-8">
            <Target className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-300 mb-2">
              Complete Your Financial Profile
            </h3>
            <p className="text-gray-400 mb-4">
              Add your income, expenses, and investment details to see personalized tax optimization strategies.
            </p>
            <Button 
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => window.location.href = '/profile'}
            >
              Complete Profile
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Total Savings Overview */}
      <Card className="bg-gradient-to-r from-green-900 to-green-800 border-green-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-green-700 rounded-full">
                <DollarSign className="w-6 h-6 text-green-100" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-green-100">
                  Total Potential Annual Savings
                </h3>
                <p className="text-3xl font-bold text-green-50">
                  ${totalSavings.toLocaleString()}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="flex items-center space-x-2 text-green-200 mb-1">
                <TrendingUp className="w-4 h-4" />
                <span className="text-sm">Optimization Opportunities</span>
              </div>
              <p className="text-2xl font-bold text-green-50">{insights.length}</p>
            </div>
          </div>
          
          {taxProfile && (
            <div className="mt-4 pt-4 border-t border-green-700">
              <div className="grid grid-cols-3 gap-4 text-green-100">
                <div>
                  <p className="text-sm text-green-300">Annual Income</p>
                  <p className="font-medium">${taxProfile.annual_income.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-green-300">Tax Bracket</p>
                  <p className="font-medium">{taxProfile.tax_bracket}%</p>
                </div>
                <div>
                  <p className="text-sm text-green-300">Filing Status</p>
                  <p className="font-medium capitalize">{taxProfile.filing_status}</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tax Optimization Strategies */}
      <Card className="bg-gray-800 border-gray-700">
        <CardHeader className="pb-4">
          <CardTitle className="text-gray-100 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Calculator className="w-5 h-5 text-blue-400" />
              <span>Tax Optimization Strategies</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchTaxInsights}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {insights.map((insight, index) => (
            <div
              key={index}
              className="border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="font-semibold text-gray-100">{insight.strategy}</h4>
                    {getDifficultyIcon(insight.difficulty)}
                    <Badge className={getDifficultyColor(insight.difficulty)}>
                      {insight.difficulty}
                    </Badge>
                    {getPriorityBadge(insight.priority)}
                  </div>
                  <p className="text-gray-400 text-sm mb-2">{insight.description}</p>
                </div>
                <div className="text-right ml-4">
                  <p className="text-sm text-gray-400">Annual Savings</p>
                  <p className="text-xl font-bold text-green-400">
                    ${insight.potentialSavings.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-4 text-sm text-gray-400">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{insight.timeline}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setExpandedInsight(expandedInsight === index ? null : index)}
                  className="text-blue-400 hover:text-blue-300 hover:bg-gray-700"
                >
                  {expandedInsight === index ? 'Hide Details' : 'Show Details'}
                </Button>
              </div>

              {expandedInsight === index && insight.implementationSteps && (
                <div className="border-t border-gray-700 pt-3 mt-3">
                  <h5 className="font-medium text-gray-200 mb-2">Implementation Steps:</h5>
                  <ul className="space-y-1">
                    {insight.implementationSteps.map((step, stepIndex) => (
                      <li key={stepIndex} className="flex items-start space-x-2 text-sm text-gray-400">
                        <span className="text-blue-400 mt-0.5">•</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Implementation Guide */}
      <Card className="bg-gray-800 border-gray-700">
        <CardHeader>
          <CardTitle className="text-gray-100 flex items-center space-x-2">
            <Target className="w-5 h-5 text-orange-400" />
            <span>Next Steps</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 border border-green-700 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <h4 className="font-medium text-green-400">Easy (Immediate)</h4>
              </div>
              <p className="text-sm text-gray-400">
                Implement these strategies right away for immediate tax savings.
              </p>
            </div>
            <div className="p-4 border border-yellow-700 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-5 h-5 text-yellow-400" />
                <h4 className="font-medium text-yellow-400">Medium (Year-End)</h4>
              </div>
              <p className="text-sm text-gray-400">
                Plan these strategies for Q4 implementation before tax deadlines.
              </p>
            </div>
            <div className="p-4 border border-red-700 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <h4 className="font-medium text-red-400">Complex (Next Year)</h4>
              </div>
              <p className="text-sm text-gray-400">
                Consult with a tax professional for advanced strategies.
              </p>
            </div>
          </div>
          
          <Separator className="bg-gray-700" />
          
          <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <Info className="w-5 h-5 text-blue-400 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-300 mb-1">Important Disclaimer</h4>
                <p className="text-sm text-gray-400">
                  These calculations are based on your current financial data and 2024 tax rules. 
                  Always consult with a qualified tax professional before implementing any tax strategies.
                </p>
              </div>
            </div>
          </div>
          
          {lastUpdated && (
            <p className="text-xs text-gray-500 text-center mt-4">
              Last updated: {lastUpdated}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TaxInsights;