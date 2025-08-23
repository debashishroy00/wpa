/**
 * WealthPath AI - Step 5: Financial Advisory Dashboard
 * Professional advisory recommendations with Step 4/5 split architecture and multi-LLM integration
 */
import React from 'react';
import EnhancedPlanEngineContainer from '../plan-engine/EnhancedPlanEngineContainer';

interface FinancialAdvisoryDashboardProps {
  onNext?: () => void;
  className?: string;
}

const FinancialAdvisoryDashboard: React.FC<FinancialAdvisoryDashboardProps> = ({ 
  onNext, 
  className = '' 
}) => {
  return (
    <EnhancedPlanEngineContainer 
      onNext={onNext}
      className={className}
    />
  );
};

export default FinancialAdvisoryDashboard;