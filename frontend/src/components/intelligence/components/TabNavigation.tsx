/**
 * WealthPath AI - Intelligence Tab Navigation
 * Navigation component for switching between analysis tabs
 */
import React from 'react';
import { 
  Eye, 
  AlertTriangle, 
  GitBranch, 
  Calendar, 
  CheckSquare,
  ChevronRight
} from 'lucide-react';
import Badge from '../../ui/Badge';

interface TabNavigationProps {
  activeTab: 'overview' | 'conflicts' | 'scenarios' | 'timeline' | 'recommendations';
  onTabChange: (tab: 'overview' | 'conflicts' | 'scenarios' | 'timeline' | 'recommendations') => void;
  conflictCount: number;
  scenarioCount: number;
  recommendationCount: number;
}

interface TabConfig {
  id: 'overview' | 'conflicts' | 'scenarios' | 'timeline' | 'recommendations';
  label: string;
  icon: React.ReactNode;
  count?: number;
  color?: string;
}

export const TabNavigation: React.FC<TabNavigationProps> = ({
  activeTab,
  onTabChange,
  conflictCount,
  scenarioCount,
  recommendationCount
}) => {
  const tabs: TabConfig[] = [
    {
      id: 'overview',
      label: 'Overview',
      icon: <Eye className="w-4 h-4" />
    },
    {
      id: 'conflicts',
      label: 'Conflicts',
      icon: <AlertTriangle className="w-4 h-4" />,
      count: conflictCount,
      color: conflictCount > 0 ? 'red' : 'gray'
    },
    {
      id: 'scenarios',
      label: 'Scenarios',
      icon: <GitBranch className="w-4 h-4" />,
      count: scenarioCount
    },
    {
      id: 'timeline',
      label: 'Timeline',
      icon: <Calendar className="w-4 h-4" />
    },
    {
      id: 'recommendations',
      label: 'Recommendations',
      icon: <CheckSquare className="w-4 h-4" />,
      count: recommendationCount,
      color: recommendationCount > 0 ? 'green' : 'gray'
    }
  ];

  const getTabClasses = (tab: TabConfig) => {
    const isActive = activeTab === tab.id;
    
    if (isActive) {
      return `
        bg-blue-600 text-white border-blue-600
        shadow-lg transform scale-105
      `;
    }
    
    return `
      bg-gray-700 text-gray-300 border-gray-600 
      hover:bg-gray-600 hover:text-white hover:border-gray-500
      transition-all duration-200
    `;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-2">
      <div className="flex flex-wrap gap-2">
        {tabs.map((tab, index) => (
          <div key={tab.id} className="flex items-center">
            <button
              onClick={() => onTabChange(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-3 rounded-lg border
                font-medium text-sm transition-all duration-200
                ${getTabClasses(tab)}
              `}
            >
              {tab.icon}
              <span>{tab.label}</span>
              
              {/* Count Badge */}
              {tab.count !== undefined && tab.count > 0 && (
                <Badge 
                  variant={tab.color === 'red' ? 'error' : 
                          tab.color === 'green' ? 'success' : 'info'}
                  size="sm"
                >
                  {tab.count}
                </Badge>
              )}
            </button>
            
            {/* Arrow indicator between tabs */}
            {index < tabs.length - 1 && (
              <ChevronRight className="w-4 h-4 text-gray-500 mx-1" />
            )}
          </div>
        ))}
      </div>
      
      {/* Tab Description */}
      <div className="mt-3 px-2">
        <p className="text-xs text-gray-400">
          {activeTab === 'overview' && 'Complete overview of your goals and their feasibility'}
          {activeTab === 'conflicts' && 'Detected conflicts between your goals and recommended resolutions'}
          {activeTab === 'scenarios' && 'Different optimization paths to achieve your goals'}
          {activeTab === 'timeline' && 'Visual timeline showing when each goal will be achieved'}
          {activeTab === 'recommendations' && 'Personalized action items to improve your success rate'}
        </p>
      </div>
    </div>
  );
};