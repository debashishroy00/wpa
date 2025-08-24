/**
 * React hooks for advisor-level data management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../utils/api-simple';

// Types
export interface AdvisorData {
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

export interface SmartRecommendation {
  id: string;
  category: string;
  title: string;
  description: string;
  currentValue?: number;
  recommendedValue?: number;
  monthlySavings?: number;
  annualSavings?: number;
  actionSteps: string[];
  difficulty: 'easy' | 'medium' | 'hard';
  timeToImplement: string;
  confidenceLevel: 'high' | 'medium' | 'low';
  assumptionsMade?: string[];
}

// Query Keys
const advisorKeys = {
  all: ['advisor'] as const,
  data: () => [...advisorKeys.all, 'data'] as const,
  recommendations: () => [...advisorKeys.all, 'recommendations'] as const,
};

// Hook: Get Current Advisor Data
export const useAdvisorData = () => {
  return useQuery({
    queryKey: advisorKeys.data(),
    queryFn: async (): Promise<AdvisorData> => {
      try {
        const data = await apiClient.get('/api/v1/advisor/advisor-data');
        return {
          // Map backend response to frontend format
          mortgageRate: data.mortgage?.interest_rate,
          mortgagePayment: data.mortgage?.monthly_payment,
          mortgageLender: data.mortgage?.lender,
          mortgageTermYears: data.mortgage?.term_years,
          mortgageStartDate: data.mortgage?.start_date,
          
          contribution401k: data.retirement?.contribution_percent,
          employerMatch: data.retirement?.employer_match,
          employerMatchLimit: data.retirement?.employer_match_limit,
          vestingSchedule: data.retirement?.vesting_schedule,
          
          stockPercentage: data.investments?.stock_percentage,
          bondPercentage: data.investments?.bond_percentage,
          averageExpenseRatio: data.investments?.average_expense_ratio,
          investmentPlatform: data.investments?.platform,
          
          subscriptions: data.subscriptions || []
        };
      } catch (error) {
        console.error('Failed to fetch advisor data:', error);
        return {};
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Hook: Save Advisor Data
export const useSaveAdvisorData = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: AdvisorData): Promise<{ status: string; updatesMade: string[] }> => {
      const requestData = {
        mortgage_rate: data.mortgageRate,
        mortgage_payment: data.mortgagePayment,
        mortgage_lender: data.mortgageLender,
        mortgage_term_years: data.mortgageTermYears,
        mortgage_start_date: data.mortgageStartDate,
        
        contribution_401k: data.contribution401k,
        employer_match: data.employerMatch,
        employer_match_limit: data.employerMatchLimit,
        vesting_schedule: data.vestingSchedule,
        
        stock_percentage: data.stockPercentage,
        bond_percentage: data.bondPercentage,
        average_expense_ratio: data.averageExpenseRatio,
        investment_platform: data.investmentPlatform,
        
        subscriptions: data.subscriptions?.map(sub => ({
          name: sub.name,
          cost: sub.cost,
          usage_frequency: sub.usage,
          can_cancel: true
        }))
      };

      return await apiClient.post('/api/v1/advisor/save-advisor-data', requestData);
    },
    onSuccess: (data) => {
      // Invalidate and refetch advisor data
      queryClient.invalidateQueries({ queryKey: advisorKeys.all });
      
      // Also invalidate financial data since we updated it
      queryClient.invalidateQueries({ queryKey: ['financial'] });
      
      console.log('Advisor data saved:', data);
    },
    onError: (error) => {
      console.error('Failed to save advisor data:', error);
    }
  });
};

// Hook: Get Smart Recommendations
export const useSmartRecommendations = () => {
  return useQuery({
    queryKey: advisorKeys.recommendations(),
    queryFn: async (): Promise<SmartRecommendation[]> => {
      try {
        const data = await apiClient.get('/api/v1/advisor/smart-recommendations');
        return data.map((rec: any) => ({
          id: rec.id,
          category: rec.category,
          title: rec.title,
          description: rec.description,
          currentValue: rec.current_value,
          recommendedValue: rec.recommended_value,
          monthlySavings: rec.monthly_savings,
          annualSavings: rec.annual_savings,
          actionSteps: rec.action_steps,
          difficulty: rec.difficulty,
          timeToImplement: rec.time_to_implement,
          confidenceLevel: rec.confidence_level,
          assumptionsMade: rec.assumptions_made
        }));
      } catch (error) {
        console.error('Failed to fetch smart recommendations:', error);
        // Return mock recommendations for development
        return [
          {
            id: 'mock-mortgage',
            category: 'mortgage',
            title: 'Potential Mortgage Refinancing',
            description: 'Based on typical rates, you might save by refinancing. Enter your rate for exact calculations.',
            currentValue: 6.5,
            recommendedValue: 5.8,
            monthlySavings: 320,
            annualSavings: 3840,
            actionSteps: [
              'Check your current mortgage statement for exact rate',
              'Get quotes from 3-5 lenders',
              'Calculate break-even point including closing costs'
            ],
            difficulty: 'medium' as const,
            timeToImplement: '30-45 days',
            confidenceLevel: 'medium' as const,
            assumptionsMade: ['Assumed 6.5% current rate based on market average']
          },
          {
            id: 'mock-401k',
            category: 'retirement',
            title: 'Maximize Employer 401k Match',
            description: 'Enter your contribution rate to see if you\'re missing free money.',
            actionSteps: [
              'Log into your 401k portal',
              'Check current contribution percentage',
              'Increase to capture full employer match'
            ],
            difficulty: 'easy' as const,
            timeToImplement: 'Next payroll cycle',
            confidenceLevel: 'high' as const,
            assumptionsMade: []
          }
        ];
      }
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Hook: Track Recommendation Action
export const useRecommendationAction = () => {
  return useMutation({
    mutationFn: async (action: {
      recommendationId: string;
      action: 'viewed' | 'started' | 'completed' | 'dismissed';
      notes?: string;
    }) => {
      // This would be implemented when we have the tracking endpoint
      console.log('Tracking recommendation action:', action);
      return action;
    },
  });
};