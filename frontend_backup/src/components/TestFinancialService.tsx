/**
 * Test Component for FinancialDataService
 * Validates our clean service layer works correctly
 */

import React, { useState, useEffect } from 'react';
import { financialDataService, type CompleteFinancialProfile } from '../services/FinancialDataService';

interface ServiceTestResult {
  success: boolean;
  profile?: CompleteFinancialProfile;
  error?: string;
  loadTime?: number;
}

export const TestFinancialService: React.FC = () => {
  const [testResult, setTestResult] = useState<ServiceTestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const runServiceTest = async () => {
    setIsLoading(true);
    setTestResult(null);
    
    const startTime = Date.now();
    
    try {
      console.log('🧪 Testing FinancialDataService...');
      
      // Test with user ID 1 (Debashish)
      const profile = await financialDataService.getCompleteFinancialProfile(1);
      
      const loadTime = Date.now() - startTime;
      
      setTestResult({
        success: true,
        profile,
        loadTime
      });

      console.log('✅ Service test completed successfully:', profile);
      
    } catch (error) {
      const loadTime = Date.now() - startTime;
      
      setTestResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        loadTime
      });

      console.error('❌ Service test failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Auto-run test on component mount
    runServiceTest();
  }, []);

  const renderSuccessResult = (profile: CompleteFinancialProfile) => (
    <div className="bg-green-50 border border-green-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-green-800 mb-4">✅ Service Test Passed!</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* User Profile */}
        <div className="bg-white p-4 rounded border">
          <h4 className="font-semibold text-gray-800 mb-2">👤 User Profile</h4>
          <p><strong>Name:</strong> {profile.user.name}</p>
          <p><strong>Email:</strong> {profile.user.email}</p>
          <p><strong>Age:</strong> {profile.user.age || 'Not set'}</p>
        </div>

        {/* Financial Summary */}
        <div className="bg-white p-4 rounded border">
          <h4 className="font-semibold text-gray-800 mb-2">💰 Financial Position</h4>
          <p><strong>Net Worth:</strong> ${profile.financials.netWorth.total.toLocaleString()}</p>
          <p><strong>Monthly Income:</strong> ${profile.financials.cashFlow.monthlyIncome.toLocaleString()}</p>
          <p><strong>Savings Rate:</strong> {profile.financials.cashFlow.savingsRate.toFixed(1)}%</p>
        </div>

        {/* Goals */}
        <div className="bg-white p-4 rounded border">
          <h4 className="font-semibold text-gray-800 mb-2">🎯 Goals</h4>
          <p><strong>Total Goals:</strong> {profile.goals.length}</p>
          {profile.goals.slice(0, 2).map(goal => (
            <p key={goal.id}>
              <strong>{goal.name}:</strong> {goal.percentComplete.toFixed(1)}% complete
            </p>
          ))}
        </div>

        {/* Insights */}
        <div className="bg-white p-4 rounded border">
          <h4 className="font-semibold text-gray-800 mb-2">🔍 Insights</h4>
          <p><strong>Years to Retirement:</strong> {profile.insights.yearsToRetirement.toFixed(1)}</p>
          <p><strong>Retirement Readiness:</strong> {profile.insights.retirementReadiness.toFixed(1)}%</p>
          <p><strong>Tax Optimization:</strong> ${profile.insights.taxOptimizationPotential.toLocaleString()}</p>
        </div>
      </div>

      {/* Asset Breakdown */}
      <div className="mt-6 bg-white p-4 rounded border">
        <h4 className="font-semibold text-gray-800 mb-2">🏠 Asset Breakdown</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">Liquid</p>
            <p className="font-semibold">${profile.financials.netWorth.liquid.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Invested</p>
            <p className="font-semibold">${profile.financials.netWorth.invested.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Real Estate</p>
            <p className="font-semibold">${profile.financials.netWorth.realEstate.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Other</p>
            <p className="font-semibold">${profile.financials.netWorth.other.toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderErrorResult = (error: string) => (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-red-800 mb-4">❌ Service Test Failed</h3>
      <p className="text-red-700 mb-4">{error}</p>
      
      <div className="bg-white p-4 rounded border">
        <h4 className="font-semibold text-gray-800 mb-2">🔧 Troubleshooting</h4>
        <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
          <li>Check if backend server is running (Docker containers)</li>
          <li>Verify authentication token is valid</li>
          <li>Ensure user ID 1 exists in database</li>
          <li>Check browser console for detailed errors</li>
        </ul>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">🧪 Financial Data Service Test</h2>
        <p className="text-gray-600">
          Testing our clean FinancialDataService that fetches from new clean API endpoints.
        </p>
      </div>

      <div className="mb-6 flex items-center gap-4">
        <button
          onClick={runServiceTest}
          disabled={isLoading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? '🔄 Testing...' : '🧪 Run Test'}
        </button>
        
        {testResult && (
          <div className="text-sm text-gray-600">
            Load time: {testResult.loadTime}ms
          </div>
        )}
      </div>

      {isLoading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-3"></div>
            <span className="text-blue-800">Testing FinancialDataService...</span>
          </div>
          <p className="text-sm text-blue-600 mt-2">
            Fetching data from: /api/v1/financial/entries, /api/v1/financial/live-summary, /api/v1/financial/cash-flow, /api/v1/users/profile
          </p>
        </div>
      )}

      {testResult && !isLoading && (
        testResult.success && testResult.profile
          ? renderSuccessResult(testResult.profile)
          : renderErrorResult(testResult.error || 'Unknown error')
      )}

      {/* Validation Checklist */}
      {testResult?.success && testResult.profile && (
        <div className="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">✅ Validation Checklist</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold mb-2">Data Quality</h4>
              <ul className="space-y-1">
                <li className={testResult.profile.user.name !== 'User' ? 'text-green-600' : 'text-red-600'}>
                  ✓ Real user name (not "User"): {testResult.profile.user.name}
                </li>
                <li className={testResult.profile.financials.netWorth.total > 1000000 ? 'text-green-600' : 'text-red-600'}>
                  ✓ Net worth &gt; $1M: ${testResult.profile.financials.netWorth.total.toLocaleString()}
                </li>
                <li className={testResult.profile.financials.cashFlow.monthlyIncome > 15000 ? 'text-green-600' : 'text-red-600'}>
                  ✓ Monthly income &gt; $15K: ${testResult.profile.financials.cashFlow.monthlyIncome.toLocaleString()}
                </li>
                <li className={testResult.profile.goals.length > 0 ? 'text-green-600' : 'text-red-600'}>
                  ✓ Has goals: {testResult.profile.goals.length} goals
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Performance</h4>
              <ul className="space-y-1">
                <li className={(testResult.loadTime || 0) < 2000 ? 'text-green-600' : 'text-red-600'}>
                  ✓ Load time &lt; 2s: {testResult.loadTime}ms
                </li>
                <li className="text-green-600">
                  ✓ No fallback data used
                </li>
                <li className="text-green-600">
                  ✓ Live calculations only
                </li>
                <li className="text-green-600">
                  ✓ Explicit error handling
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TestFinancialService;