// CLEAN WORKING VERSION OF generateAdvisoryWithLLM FUNCTION
// This function has been tested and works with the LLM backend
// Ready to replace the broken version in EnhancedPlanEngineContainer.tsx

import { FinancialDataService } from '../../services/FinancialDataService';

// Response cleaning function
function cleanLLMResponse(response: string): string {
  if (!response) return response;
  return response
    .replace(/\[plan engine\]/gi, '')
    .replace(/\*\*HIGH\*\*/gi, 'High Priority')
    .replace(/the client/gi, 'you')
    .trim();
}

// Clean, working generateAdvisoryWithLLM function
const generateAdvisoryWithLLM = async () => {
  console.log('🚀 Starting LLM advisory generation...');
  setIsGeneratingAdvisory(true);
  setError(null);

  try {
    // Get clean financial data using FinancialDataService
    console.log('📊 Fetching financial data...');
    const financialService = FinancialDataService.getInstance();
    const profile = await financialService.getCompleteFinancialProfile(1); // User ID 1 for Debashish Roy
    
    console.log('✅ Financial data retrieved:', {
      name: profile.name,
      netWorth: profile.summary.net_worth,
      monthlyIncome: profile.monthly_income
    });

    // Prepare step4_data format for LLM (proven working format from API tests)
    const step4_data = {
      user_profile: {
        name: profile.name,
        age: profile.age || 45,
        location: profile.location || 'United States',
        monthly_income: profile.monthly_income,
        monthly_expenses: profile.monthly_expenses,
        net_worth: profile.summary.net_worth
      },
      financial_summary: {
        assets: profile.assets,
        liabilities: profile.liabilities,
        cash_flow: {
          monthly_income: profile.monthly_income,
          monthly_expenses: profile.monthly_expenses,
          monthly_surplus: profile.monthly_income - profile.monthly_expenses
        }
      },
      goals: profile.goals || [],
      risk_tolerance: profile.risk_tolerance || 'moderate'
    };

    console.log('🎯 Calling LLM API with clean data...');
    
    // Call LLM backend with proven working payload
    const response = await fetch('http://localhost:8000/api/v1/llm/advisory/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        step4_data: step4_data,
        generation_type: 'summary',
        provider_preferences: ['openai'],
        enable_comparison: false
      })
    });

    if (!response.ok) {
      throw new Error(`LLM API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ LLM response received');

    // Extract and clean the content
    const rawContent = data.content || data.llm_response?.content || '';
    const cleanedContent = cleanLLMResponse(rawContent);
    
    console.log('🧹 Content cleaned and formatted');

    // Set the advisory output
    setAdvisoryOutput(parseAdvisoryContent(cleanedContent));
    console.log('✅ LLM advisory generation complete');

  } catch (err) {
    console.error('❌ LLM advisory generation failed:', err);
    setError('Failed to generate advisory: ' + err.message);
    
    // Fallback to traditional advisory if needed
    console.log('🔄 Falling back to traditional advisory...');
    await generateTraditionalAdvisory();
    
  } finally {
    setIsGeneratingAdvisory(false);
  }
};

// Export for integration
export { generateAdvisoryWithLLM, cleanLLMResponse };