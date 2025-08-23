/**
 * Citation Tooltip Component
 * Shows source information on hover
 */
import React, { useState } from 'react';

interface CitationTooltipProps {
  citationId: string;
  isKnowledgeBase: boolean;
  isViewed: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

const CitationTooltip: React.FC<CitationTooltipProps> = ({
  citationId,
  isKnowledgeBase,
  isViewed,
  onClick,
  children
}) => {
  const [isVisible, setIsVisible] = useState(false);

  const getTooltipContent = () => {
    if (!isKnowledgeBase) {
      return {
        title: 'Plan Engine Calculation',
        description: 'Data sourced from Step 4 deterministic calculations',
        type: 'calculation'
      };
    }

    // Map KB-IDs to their descriptions
    const kbMap: Record<string, { title: string; description: string; category: string }> = {
      'AL-001': {
        title: 'Asset Location Strategy',
        description: 'Tax-efficient account placement guidelines',
        category: 'Tax Optimization'
      },
      'RB-001': {
        title: 'Rebalancing Strategy',
        description: 'Portfolio rebalancing best practices',
        category: 'Portfolio Management'
      },
      'DP-001': {
        title: 'Debt Payoff Strategy',
        description: 'Avalanche vs snowball debt elimination methods',
        category: 'Debt Management'
      },
      'IRS-001': {
        title: 'IRS Contribution Limits',
        description: 'Current year contribution limits and tax rules',
        category: 'Tax Regulations'
      },
      'AA-001': {
        title: 'Asset Allocation Research',
        description: 'Academic research on portfolio allocation',
        category: 'Investment Research'
      }
    };

    const info = kbMap[citationId] || {
      title: 'Knowledge Base Document',
      description: 'Financial advisory knowledge source',
      category: 'Reference'
    };

    return {
      title: info.title,
      description: info.description,
      type: 'knowledge_base',
      category: info.category
    };
  };

  const tooltipContent = getTooltipContent();

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={onClick}
      >
        {children}
      </div>

      {isVisible && (
        <div className="absolute z-50 bottom-full left-1/2 transform -translate-x-1/2 mb-2">
          <div className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-sm shadow-xl max-w-xs">
            {/* Arrow */}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2">
              <div className="border-4 border-transparent border-t-gray-800"></div>
            </div>

            {/* Content */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-white">
                  {tooltipContent.title}
                </span>
                {tooltipContent.type === 'knowledge_base' && (
                  <span className="text-xs px-1.5 py-0.5 bg-blue-600 text-blue-100 rounded">
                    {tooltipContent.category}
                  </span>
                )}
              </div>
              
              <p className="text-gray-300 text-xs">
                {tooltipContent.description}
              </p>
              
              {isKnowledgeBase && (
                <div className="flex items-center justify-between pt-1 mt-2 border-t border-gray-600">
                  <span className="text-xs text-gray-400">
                    {isViewed ? 'Viewed' : 'Click to view'}
                  </span>
                  <span className="text-xs text-blue-400">
                    [{citationId}]
                  </span>
                </div>
              )}
              
              {!isKnowledgeBase && (
                <div className="pt-1 mt-2 border-t border-gray-600">
                  <span className="text-xs text-purple-400">
                    Step 4 Calculation Source
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CitationTooltip;