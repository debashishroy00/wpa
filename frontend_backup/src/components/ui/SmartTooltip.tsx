/**
 * WealthPath AI - Smart Tooltip with Knowledge Base Integration
 * Provides contextual help with professional backing
 */
import React, { useState } from 'react';
import { HelpCircle, BookOpen, ExternalLink } from 'lucide-react';
import CitationModal from '../plan-engine/CitationModal';

interface SmartTooltipProps {
  content: string;
  kbSource?: string;
  detailedInfo?: string;
  children: React.ReactNode;
  className?: string;
}

export const SmartTooltip: React.FC<SmartTooltipProps> = ({
  content,
  kbSource,
  detailedInfo,
  children,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showCitationModal, setShowCitationModal] = useState(false);

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => {
          setIsVisible(false);
          setShowDetails(false);
        }}
        className="cursor-help"
      >
        {children}
      </div>
      
      {isVisible && (
        <div className="absolute z-50 w-80 p-4 bg-gray-800 border border-gray-600 rounded-lg shadow-xl bottom-full left-1/2 transform -translate-x-1/2 mb-2">
          {/* Arrow */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
          
          {/* Main Content */}
          <div className="text-sm text-gray-200 mb-3">
            {content}
          </div>
          
          {/* Knowledge Base Source */}
          {kbSource && (
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="w-3 h-3 text-blue-400" />
              <span className="text-xs text-blue-400 font-medium">Source: {kbSource}</span>
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-xs text-gray-400">Professional Guidance</span>
            </div>
            
            <div className="flex gap-2">
              {detailedInfo && (
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  {showDetails ? 'Hide Details' : 'Learn More'}
                </button>
              )}
              {kbSource && (
                <button
                  onClick={() => {
                    setIsVisible(false);
                    setShowCitationModal(true);
                  }}
                  className="text-xs text-green-400 hover:text-green-300 flex items-center gap-1"
                >
                  <BookOpen className="w-3 h-3" />
                  View Source
                </button>
              )}
            </div>
          </div>
          
          {/* Detailed Information */}
          {showDetails && detailedInfo && (
            <div className="mt-3 pt-3 border-t border-gray-600">
              <div className="text-xs text-gray-300">
                {detailedInfo}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Citation Modal */}
      {showCitationModal && kbSource && (
        <CitationModal
          citationId={kbSource.split(':')[0]} // Extract KB ID from "KB-001: Title" format
          onClose={() => setShowCitationModal(false)}
        />
      )}
    </div>
  );
};

// Helper component for inline help icons
export const HelpIcon: React.FC<{ tooltip: string; kbSource?: string; className?: string }> = ({
  tooltip,
  kbSource,
  className = ''
}) => {
  return (
    <SmartTooltip content={tooltip} kbSource={kbSource} className={className}>
      <HelpCircle className="w-4 h-4 text-gray-400 hover:text-gray-300 transition-colors" />
    </SmartTooltip>
  );
};

export default SmartTooltip;