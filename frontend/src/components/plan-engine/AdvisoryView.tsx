/**
 * Step 5: Advisory Report View Component
 * Displays professional financial advice with citations
 */
import React, { useState } from 'react';
import { FileText, Download, ExternalLink, CheckCircle, Clock, AlertTriangle, Target, TrendingUp } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import CitationTooltip from './CitationTooltip';
import CitationModal from './CitationModal';

interface AdvisoryOutput {
  executive_summary: string[];
  immediate_actions: Array<{
    text: string;
    priority: 'high' | 'medium' | 'low';
    category: string;
    timeline: string;
  }>;
  twelve_month_strategy: Array<{
    text: string;
    priority: 'high' | 'medium' | 'low';
    category: string;
    timeline: string;
  }>;
  risk_management: Array<{
    text: string;
    priority: 'high' | 'medium' | 'low';
    category: string;
    timeline: string;
  }>;
  tax_considerations: Array<{
    text: string;
    priority: 'high' | 'medium' | 'low';
    category: string;
    timeline: string;
  }>;
  citations: string[];
  disclaimers: string[];
  plan_data_sources: string[];
  generation_timestamp: string;
}

interface AdvisoryViewProps {
  advisoryOutput: AdvisoryOutput;
  planOutput: any; // Plan engine output for context
  className?: string;
}

const AdvisoryView: React.FC<AdvisoryViewProps> = ({ 
  advisoryOutput, 
  planOutput, 
  className = '' 
}) => {
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null);
  const [viewedCitations, setViewedCitations] = useState<Set<string>>(new Set());

  // Debug the data structure being passed
  console.log('AdvisoryView props:', { advisoryOutput, planOutput });
  console.log('Advisory data structure:', advisoryOutput);

  // Emergency helper function to safely extract text from any value
  const extractText = (item: any): string => {
    if (!item) return '';
    if (typeof item === 'string') return item;
    if (typeof item === 'object' && item.text) return item.text;
    if (typeof item === 'object') return JSON.stringify(item);
    return String(item);
  };

  // Process and clean LLM content for proper display
  const processLLMContent = (content: string): string => {
    if (!content || typeof content !== 'string') return '';
    
    return content
      // Fix section breaks
      .replace(/## /g, '\n## ')
      .replace(/### /g, '\n### ')
      // Remove misplaced priority badges from text
      .replace(/\*\*HIGH\*\*([a-z]+)/gi, '')
      .replace(/\*\*MEDIUM\*\*([a-z]+)/gi, '')
      .replace(/\*\*LOW\*\*([a-z]+)/gi, '')
      .replace(/HIGH([a-z]+)/gi, '')
      .replace(/MEDIUM([a-z]+)/gi, '')
      .replace(/LOW([a-z]+)/gi, '')
      // Clean up extra spaces and line breaks
      .replace(/\s+/g, ' ')
      .replace(/\n\s+/g, '\n')
      // Ensure proper citation formatting
      .replace(/\[plan engine\]/g, '[plan engine]')
      .replace(/\[KB-(\d+)\]/g, '[KB-$1]')
      .trim();
  };

  // Safety check: Don't render if advisoryOutput is null/undefined
  if (!advisoryOutput) {
    return (
      <div className={`bg-gray-900 text-white p-6 rounded-lg ${className}`}>
        <div className="text-center">
          <div className="text-gray-400 mb-4">Loading advisory report...</div>
          <div className="animate-pulse">
            <div className="h-4 bg-gray-700 rounded w-3/4 mx-auto mb-2"></div>
            <div className="h-4 bg-gray-700 rounded w-1/2 mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  const handleCitationClick = (citationId: string) => {
    setSelectedCitation(citationId);
    setViewedCitations(prev => new Set([...prev, citationId]));
  };

  const formatDate = (timestamp: string | undefined | null) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleString();
    } catch (e) {
      console.warn('Invalid timestamp:', timestamp);
      return 'Invalid Date';
    }
  };

  const handleExportPDF = () => {
    // This would integrate with a PDF generation service
    // For now, we'll create a simplified HTML export
    const htmlContent = generateHTMLReport();
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `advisory-report-${new Date().toISOString().split('T')[0]}.html`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const generateHTMLReport = (): string => {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>WealthPath AI Advisory Report</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }
        .section { margin: 30px 0; }
        .citation { color: #0066cc; text-decoration: none; }
        .disclaimer { font-size: 0.9em; color: #666; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Financial Advisory Report</h1>
        <p>Generated: ${formatDate(advisoryOutput.generation_timestamp)}</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        ${(advisoryOutput.executive_summary || []).map(item => `<p>${item}</p>`).join('')}
    </div>
    
    <div class="section">
        <h2>Immediate Actions (Next 30 Days)</h2>
        <ul>
            ${(advisoryOutput.immediate_actions || []).map(action => `<li>${action.text}</li>`).join('')}
        </ul>
    </div>
    
    <div class="section">
        <h2>12-Month Strategy</h2>
        <ul>
            ${(advisoryOutput.twelve_month_strategy || []).map(item => `<li>${item.text}</li>`).join('')}
        </ul>
    </div>
    
    <div class="disclaimers">
        <h3>Important Disclaimers</h3>
        ${(advisoryOutput.disclaimers || []).map(disclaimer => `<p>${disclaimer}</p>`).join('')}
    </div>
</body>
</html>
    `;
  };

  const renderCitation = (text: any) => {
    // Parse text for citations like [KB-001] or [plan engine]
    const rawText = extractText(text);
    const cleanText = processLLMContent(rawText);
    
    if (!cleanText || typeof cleanText !== 'string') {
      console.warn('Invalid text for renderCitation:', text);
      return rawText;
    }
    
    const citationRegex = /\[([\w\s-]+)\]/g;
    
    return cleanText.split(citationRegex).map((part, index) => {
      if (index % 2 === 1) {
        // This is a citation
        const isKnowledgeBase = part.includes('-');
        const isViewed = viewedCitations.has(part);
        
        return (
          <CitationTooltip
            key={index}
            citationId={part}
            isKnowledgeBase={isKnowledgeBase}
            isViewed={isViewed}
            onClick={() => handleCitationClick(part)}
          >
            <span
              className={`
                inline-flex items-center px-1.5 py-0.5 text-xs font-medium rounded cursor-pointer
                transition-all duration-200 hover:scale-105
                ${isKnowledgeBase 
                  ? isViewed 
                    ? 'bg-green-800 text-green-200 border border-green-600' 
                    : 'bg-blue-800 text-blue-200 border border-blue-600 hover:bg-blue-700'
                  : 'bg-purple-800 text-purple-200 border border-purple-600'
                }
              `}
            >
              [{part}]
              {!isViewed && isKnowledgeBase && (
                <ExternalLink className="w-3 h-3 ml-1" />
              )}
            </span>
          </CitationTooltip>
        );
      }
      return part;
    });
  };

  const getPriorityColor = (priority: 'high' | 'medium' | 'low') => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTimelineIcon = (timeline: string) => {
    switch (timeline) {
      case '30_days': return <Clock className="w-4 h-4" />;
      case 'quarterly': return <Target className="w-4 h-4" />;
      case 'annual': return <TrendingUp className="w-4 h-4" />;
      default: return <CheckCircle className="w-4 h-4" />;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <FileText className="w-6 h-6 text-green-500" />
            Step 5: Professional Advisory Report
          </h2>
          <p className="text-gray-400 mt-1">
            Fiduciary financial guidance based on your plan calculations
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-400">
            <Clock className="w-4 h-4 inline mr-1" />
            {formatDate(advisoryOutput.generation_timestamp)}
          </div>
          <Button onClick={handleExportPDF} className="bg-green-600 hover:bg-green-700">
            <Download className="w-4 h-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Supporting Data Summary */}
      <Card className="border-green-600 bg-green-900/20">
        <Card.Body>
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
            <div>
              <h4 className="text-green-400 font-medium">Advisory Analysis Complete</h4>
              <p className="text-green-200 text-sm mt-1">
                This professional advisory report is based on your Step 4 plan calculations: {' '}
                <strong>{(planOutput?.gap_analysis?.monte_carlo_success_rate * 100 || 0).toFixed(1)}%</strong> success rate, {' '}
                <strong>${planOutput?.contribution_schedule?.total_monthly?.toLocaleString() || '0'}</strong> monthly savings required.
                All recommendations cite either plan engine calculations or knowledge base sources.
              </p>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Executive Summary */}
      <Card>
        <Card.Body>
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-500" />
            Executive Summary
          </h3>
          <div className="space-y-3">
            {(advisoryOutput.executive_summary || []).map((summary, index) => (
              <p key={index} className="text-gray-300 leading-relaxed">
                {renderCitation(extractText(summary))}
              </p>
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* Immediate Actions */}
      <Card>
        <Card.Body>
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-red-500" />
            Immediate Actions (Next 30 Days)
          </h3>
          <div className="space-y-4">
            {(advisoryOutput.immediate_actions || []).map((action, index) => (
              <div key={index} className="flex items-start gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
                <div className="flex-shrink-0">
                  {getTimelineIcon(action.timeline)}
                </div>
                <div className="flex-grow">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={getPriorityColor(action.priority)}>
                      {action.priority.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-gray-400">{action.category}</span>
                  </div>
                  <p className="text-gray-300 leading-relaxed">
                    {renderCitation(extractText(action.text))}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* 12-Month Strategy */}
      <Card>
        <Card.Body>
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-purple-500" />
            12-Month Strategy
          </h3>
          <div className="space-y-4">
            {(advisoryOutput.twelve_month_strategy || []).map((strategy, index) => (
              <div key={index} className="flex items-start gap-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
                <div className="flex-shrink-0">
                  {getTimelineIcon(strategy.timeline)}
                </div>
                <div className="flex-grow">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={getPriorityColor(strategy.priority)}>
                      {strategy.priority.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-gray-400">{strategy.category}</span>
                  </div>
                  <p className="text-gray-300 leading-relaxed">
                    {renderCitation(extractText(strategy.text))}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* Risk Management */}
      <Card>
        <Card.Body>
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            Risk Management
          </h3>
          <div className="space-y-3">
            {(advisoryOutput.risk_management || []).map((risk, index) => (
              <p key={index} className="text-gray-300 leading-relaxed">
                {renderCitation(extractText(risk.text))}
              </p>
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* Tax Considerations */}
      <Card>
        <Card.Body>
          <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-500" />
            Tax Considerations
          </h3>
          <div className="space-y-3">
            {(advisoryOutput.tax_considerations || []).map((tax, index) => (
              <p key={index} className="text-gray-300 leading-relaxed">
                {renderCitation(extractText(tax.text))}
              </p>
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* Citations & Sources */}
      <Card className="border-gray-600">
        <Card.Body>
          <h3 className="text-lg font-semibold text-white mb-4">Sources & Citations</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2">Knowledge Base Sources</h4>
              <div className="space-y-1">
                {(advisoryOutput.citations || []).filter(c => extractText(c).includes('-')).map((citation, index) => (
                  <button
                    key={index}
                    onClick={() => handleCitationClick(extractText(citation))}
                    className={`
                      block text-sm px-2 py-1 rounded text-left w-full transition-colors
                      ${viewedCitations.has(extractText(citation)) 
                        ? 'text-green-400 bg-green-900/20' 
                        : 'text-blue-400 hover:bg-blue-900/20'
                      }
                    `}
                  >
                    [{extractText(citation)}] {viewedCitations.has(extractText(citation)) ? '✓' : '→'}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-300 mb-2">Plan Engine Sources</h4>
              <div className="space-y-1">
                {(advisoryOutput.plan_data_sources || []).map((source, index) => (
                  <div key={index} className="text-sm text-purple-400 px-2 py-1">
                    • {extractText(source).replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>

      {/* Disclaimers */}
      <Card className="border-yellow-600 bg-yellow-900/20">
        <Card.Body>
          <h3 className="text-lg font-semibold text-yellow-400 mb-3">Important Disclaimers</h3>
          <div className="space-y-2">
            {(advisoryOutput.disclaimers || []).map((disclaimer, index) => (
              <p key={index} className="text-yellow-200 text-sm">
                • {extractText(disclaimer)}
              </p>
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* Citation Modal */}
      {selectedCitation && (
        <CitationModal
          citationId={selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </div>
  );
};

export default AdvisoryView;