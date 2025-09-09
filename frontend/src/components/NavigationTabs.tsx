import React from 'react';

interface Tab {
  id: string;
  label: string;
  view: string;
}

interface NavigationTabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabClick: (view: string) => void;
  className?: string;
}

const NavigationTabs: React.FC<NavigationTabsProps> = ({ 
  tabs, 
  activeTab, 
  onTabClick, 
  className = '' 
}) => {
  return (
    <div className={`bg-gray-950 border-b-2 border-gray-600 relative z-10 mb-0 ${className}`}>
      <div className="container mx-auto px-4">
        <div className="flex space-x-1 overflow-x-auto overflow-y-hidden scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-600 hover:scrollbar-thumb-gray-500">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => onTabClick(tab.view)}
              className={`px-6 py-4 text-base font-bold transition-all duration-200 whitespace-nowrap
                ${activeTab === tab.id 
                  ? 'text-white border-b-4 border-blue-400 bg-blue-900/40' 
                  : 'text-gray-300 hover:text-white hover:bg-gray-800/50 hover:border-b-2 hover:border-gray-500 border-transparent'
                }
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NavigationTabs;