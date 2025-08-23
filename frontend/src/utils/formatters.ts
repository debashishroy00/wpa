/**
 * Enhanced number and currency formatting utilities for production UI
 */

export const formatCurrency = (amount: number, compact = false): string => {
  if (compact && amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`;
  }
  if (compact && amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}k`;
  }
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(Math.round(amount));
};

export const formatNumber = (value: number, decimals = 0): string => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatPercentage = (num: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(num / 100);
};

export const getAmountColor = (amount: number): string => {
  return amount >= 0 ? 'text-green-600' : 'text-red-600';
};

export const getImpactBadge = (action: string): { effort: string; impact: string; effortColor: string; impactColor: string } => {
  // Simple heuristic for demo - in production would be from LLM or predefined rules
  const lowEffortWords = ['review', 'check', 'compare', 'research'];
  const highImpactWords = ['maximize', 'payoff', 'contribute', 'invest', 'rebalance'];
  
  const actionLower = action.toLowerCase();
  const isLowEffort = lowEffortWords.some(word => actionLower.includes(word));
  const isHighImpact = highImpactWords.some(word => actionLower.includes(word));
  
  const effort = isLowEffort ? 'Low' : 'Medium';
  const impact = isHighImpact ? 'High' : 'Medium';
  
  return {
    effort,
    impact,
    effortColor: effort === 'Low' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800',
    impactColor: impact === 'High' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
  };
};