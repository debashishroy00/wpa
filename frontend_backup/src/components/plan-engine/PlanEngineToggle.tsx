/**
 * Step 4/5 View Toggle Component
 * Switches between raw calculation data and advisory report
 */
import React from 'react';
import { Code, FileText, Eye } from 'lucide-react';
import Button from '../ui/Button';

export type ViewMode = 'raw_data' | 'advisory_report';

interface PlanEngineToggleProps {
  currentView: ViewMode;
  onViewChange: (view: ViewMode) => void;
  className?: string;
  showViewIndicator?: boolean;
}

const PlanEngineToggle: React.FC<PlanEngineToggleProps> = ({
  currentView,
  onViewChange,
  className = '',
  showViewIndicator = true
}) => {
  return (
    <div className={`flex items-center gap-4 ${className}`}>
      {/* View Mode Toggle */}
      <div className="flex bg-gray-800 rounded-lg p-1 border border-gray-700">
        <button
          onClick={() => onViewChange('raw_data')}
          className={`
            flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
            ${currentView === 'raw_data'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'text-gray-300 hover:text-white hover:bg-gray-700'
            }
          `}
        >
          <Code className="w-4 h-4" />
          Raw Data
        </button>
        
        <button
          onClick={() => onViewChange('advisory_report')}
          className={`
            flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-all duration-200
            ${currentView === 'advisory_report'
              ? 'bg-green-600 text-white shadow-sm'
              : 'text-gray-300 hover:text-white hover:bg-gray-700'
            }
          `}
        >
          <FileText className="w-4 h-4" />
          Advisory Report
        </button>
      </div>

      {/* View Mode Indicator */}
      {showViewIndicator && (
        <div className="flex items-center gap-2 text-sm">
          <Eye className="w-4 h-4 text-gray-400" />
          <span className="text-gray-400">
            Viewing: 
            <span className={`ml-1 font-medium ${
              currentView === 'raw_data' ? 'text-blue-400' : 'text-green-400'
            }`}>
              {currentView === 'raw_data' ? 'Pure Calculations' : 'Professional Advice'}
            </span>
          </span>
        </div>
      )}
    </div>
  );
};

export default PlanEngineToggle;