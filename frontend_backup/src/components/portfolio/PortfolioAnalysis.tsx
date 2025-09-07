/**
 * WealthPath AI - Portfolio Analysis Component
 * Leverages existing asset data for intelligent portfolio recommendations
 */
import React from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip,
  Legend 
} from 'recharts';
import { 
  TrendingUp, 
  AlertTriangle, 
  Target, 
  DollarSign,
  BarChart3,
  Info
} from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

interface AssetBreakdown {
  category: string;
  amount: number;
  percentage: number;
  color: string;
  riskLevel: 'Low' | 'Medium' | 'High';
  liquidity: 'Low' | 'Medium' | 'High';
}

interface PortfolioAnalysisProps {
  totalAssets: number;
  riskTolerance: number; // 1-10 scale
  age?: number;
}

// Calculate portfolio breakdown from existing financial data
const calculatePortfolioBreakdown = (totalAssets: number): AssetBreakdown[] => {
  // Based on the captured data from architecture directive
  const assetData = [
    {
      category: 'Real Estate',
      amount: 1152500, // Primary $650K + Rental $450K + REITs $52.5K
      color: '#10B981', // emerald-500
      riskLevel: 'Medium' as const,
      liquidity: 'Low' as const
    },
    {
      category: 'Stocks',
      amount: 315000, // Individual $125K + ETFs $90K + Mutual $100K
      color: '#3B82F6', // blue-500
      riskLevel: 'High' as const,
      liquidity: 'High' as const
    },
    {
      category: 'Retirement',
      amount: 300000, // 401k $185K + IRA $115K
      color: '#8B5CF6', // purple-500
      riskLevel: 'Medium' as const,
      liquidity: 'Low' as const
    },
    {
      category: 'Bonds',
      amount: 80000, // Bond ETFs $45K + Bond Funds $35K
      color: '#F59E0B', // amber-500
      riskLevel: 'Low' as const,
      liquidity: 'Medium' as const
    },
    {
      category: 'Cash',
      amount: 72300, // Savings $35K + Checking $12.3K + MM $25K
      color: '#6B7280', // gray-500
      riskLevel: 'Low' as const,
      liquidity: 'High' as const
    },
    {
      category: 'Alternative',
      amount: 17700, // Crypto $5.5K + Commodities $12.2K
      color: '#EF4444', // red-500
      riskLevel: 'High' as const,
      liquidity: 'Medium' as const
    }
  ];

  return assetData.map(asset => ({
    ...asset,
    percentage: Math.round((asset.amount / totalAssets) * 100)
  }));
};

// Calculate target allocation based on risk tolerance and age
const calculateTargetAllocation = (riskTolerance: number, age: number = 38) => {
  // For risk tolerance 7/10 at age 38 (from directive)
  const stocksTarget = Math.min(90, riskTolerance * 10); // 70%
  const bondsTarget = Math.max(5, (10 - riskTolerance) * 2); // 6%
  const realEstateTarget = 20; // Reasonable allocation
  const cashTarget = 2; // Emergency fund only
  const alternativeTarget = 2; // Small allocation
  
  return [
    { category: 'Stocks', target: stocksTarget, color: '#3B82F6' },
    { category: 'Real Estate', target: realEstateTarget, color: '#10B981' },
    { category: 'Bonds', target: bondsTarget, color: '#F59E0B' },
    { category: 'Cash', target: cashTarget, color: '#6B7280' },
    { category: 'Alternative', target: alternativeTarget, color: '#EF4444' }
  ];
};

// Generate specific rebalancing recommendations
const generateRebalancingRecommendations = (
  current: AssetBreakdown[], 
  target: any[], 
  totalAssets: number
) => {
  const recommendations = [];
  
  // Real Estate concentration risk
  const realEstate = current.find(c => c.category === 'Real Estate');
  const realEstateTarget = target.find(t => t.category === 'Real Estate');
  
  if (realEstate && realEstateTarget && realEstate.percentage > realEstateTarget.target + 10) {
    const excessAmount = (realEstate.percentage - realEstateTarget.target) * totalAssets / 100;
    recommendations.push({
      type: 'reduce',
      asset: 'Real Estate',
      current: realEstate.percentage,
      target: realEstateTarget.target,
      action: 'Sell rental property or convert to REITs',
      amount: excessAmount,
      impact: 'Reduce concentration risk, increase liquidity',
      priority: 'High'
    });
  }
  
  // Stock underallocation
  const stocks = current.find(c => c.category === 'Stocks');
  const stocksTarget = target.find(t => t.category === 'Stocks');
  
  if (stocks && stocksTarget && stocks.percentage < stocksTarget.target - 10) {
    const shortfallAmount = (stocksTarget.target - stocks.percentage) * totalAssets / 100;
    recommendations.push({
      type: 'increase',
      asset: 'Stocks',
      current: stocks.percentage,
      target: stocksTarget.target,
      action: 'Reallocate from real estate and cash to stock index funds',
      amount: shortfallAmount,
      impact: 'Increase expected returns by 2.3% annually',
      priority: 'High'
    });
  }
  
  return recommendations;
};

const PortfolioAnalysis: React.FC<PortfolioAnalysisProps> = ({ 
  totalAssets, 
  riskTolerance, 
  age = 38 
}) => {
  const currentAllocation = calculatePortfolioBreakdown(totalAssets);
  const targetAllocation = calculateTargetAllocation(riskTolerance, age);
  const recommendations = generateRebalancingRecommendations(currentAllocation, targetAllocation, totalAssets);
  
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Prepare data for comparison chart
  const comparisonData = targetAllocation.map(target => {
    const current = currentAllocation.find(c => c.category === target.category);
    return {
      category: target.category,
      current: current?.percentage || 0,
      target: target.target,
      gap: target.target - (current?.percentage || 0)
    };
  });

  // Check for concentration risk
  const maxAllocation = Math.max(...currentAllocation.map(a => a.percentage));
  const hasConcentrationRisk = maxAllocation > 40;
  const concentratedAsset = currentAllocation.find(a => a.percentage === maxAllocation);

  return (
    <div className="space-y-6">
      {/* Concentration Risk Warning */}
      {hasConcentrationRisk && concentratedAsset && (
        <Card className="bg-gradient-to-r from-red-900/20 to-orange-900/20 border-red-600">
          <Card.Body className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-red-100 font-semibold mb-1">Concentration Risk Alert</h4>
                <p className="text-red-200 text-sm">
                  {concentratedAsset.percentage}% of your portfolio is in {concentratedAsset.category}. 
                  This creates significant risk if this asset class underperforms.
                </p>
              </div>
            </div>
          </Card.Body>
        </Card>
      )}

      {/* Current Portfolio Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <Card.Body className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              Current Portfolio Allocation
            </h3>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={currentAllocation}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ category, percentage }) => `${category}: ${percentage}%`}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="percentage"
                  >
                    {currentAllocation.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: any, name: any) => [
                      `${value}% (${formatCurrency(currentAllocation.find(a => a.category === name)?.amount || 0)})`, 
                      name
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card.Body>
        </Card>

        <Card>
          <Card.Body className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-green-400" />
              Current vs Target Allocation
            </h3>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="category" 
                    stroke="#9CA3AF"
                    fontSize={12}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1F2937', border: 'none' }}
                    formatter={(value: any, name: any) => [`${value}%`, name === 'current' ? 'Current' : 'Target']}
                  />
                  <Legend />
                  <Bar dataKey="current" fill="#EF4444" name="Current" />
                  <Bar dataKey="target" fill="#10B981" name="Target" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card.Body>
        </Card>
      </div>

      {/* Portfolio Details Table */}
      <Card>
        <Card.Body className="p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Portfolio Breakdown Details</h3>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-2 text-gray-300">Asset Class</th>
                  <th className="text-right py-3 px-2 text-gray-300">Amount</th>
                  <th className="text-right py-3 px-2 text-gray-300">Current %</th>
                  <th className="text-right py-3 px-2 text-gray-300">Target %</th>
                  <th className="text-center py-3 px-2 text-gray-300">Risk</th>
                  <th className="text-center py-3 px-2 text-gray-300">Liquidity</th>
                </tr>
              </thead>
              <tbody>
                {currentAllocation.map(asset => {
                  const target = targetAllocation.find(t => t.category === asset.category);
                  const isOverweight = target && asset.percentage > target.target + 5;
                  const isUnderweight = target && asset.percentage < target.target - 5;
                  
                  return (
                    <tr key={asset.category} className="border-b border-gray-800">
                      <td className="py-3 px-2">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: asset.color }}
                          />
                          <span className="text-white font-medium">{asset.category}</span>
                        </div>
                      </td>
                      <td className="py-3 px-2 text-right text-white">
                        {formatCurrency(asset.amount)}
                      </td>
                      <td className="py-3 px-2 text-right">
                        <span className={`font-medium ${
                          isOverweight ? 'text-red-400' : 
                          isUnderweight ? 'text-yellow-400' : 'text-white'
                        }`}>
                          {asset.percentage}%
                        </span>
                      </td>
                      <td className="py-3 px-2 text-right text-gray-300">
                        {target ? `${target.target}%` : '-'}
                      </td>
                      <td className="py-3 px-2 text-center">
                        <Badge 
                          variant={
                            asset.riskLevel === 'High' ? 'danger' : 
                            asset.riskLevel === 'Medium' ? 'warning' : 'success'
                          }
                          size="sm"
                        >
                          {asset.riskLevel}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 text-center">
                        <Badge 
                          variant={
                            asset.liquidity === 'High' ? 'success' : 
                            asset.liquidity === 'Medium' ? 'warning' : 'secondary'
                          }
                          size="sm"
                        >
                          {asset.liquidity}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card.Body>
      </Card>

      {/* Rebalancing Recommendations */}
      {recommendations.length > 0 && (
        <Card className="bg-gradient-to-r from-blue-900/20 to-purple-900/20 border-blue-600">
          <Card.Body className="p-6">
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-400" />
              Portfolio Rebalancing Recommendations
            </h3>
            
            <div className="space-y-4">
              {recommendations.map((rec, index) => (
                <div key={index} className="border border-gray-700 rounded-lg p-4 bg-gray-800/50">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <Badge 
                        variant={rec.priority === 'High' ? 'danger' : 'warning'} 
                        size="sm"
                      >
                        {rec.priority} Priority
                      </Badge>
                      <h4 className="font-semibold text-white">
                        {rec.type === 'reduce' ? 'Reduce' : 'Increase'} {rec.asset} Allocation
                      </h4>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-400">
                        {rec.current}% → {rec.target}%
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-gray-300 mb-3">{rec.action}</p>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Amount to Rebalance:</span>
                      <div className="text-white font-medium">{formatCurrency(rec.amount)}</div>
                    </div>
                    <div>
                      <span className="text-gray-400">Expected Impact:</span>
                      <div className="text-green-400">{rec.impact}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex gap-3">
              <Button className="bg-green-600 hover:bg-green-700">
                <DollarSign className="w-4 h-4 mr-2" />
                Apply Recommendations
              </Button>
              <Button variant="outline">
                <Info className="w-4 h-4 mr-2" />
                Learn More About Rebalancing
              </Button>
            </div>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default PortfolioAnalysis;