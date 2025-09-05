/**
 * WealthPath AI - Knowledge Base Insights Component
 * Shows contextual professional insights based on user's financial situation
 */
import React, { useState, useEffect } from 'react';
import { BookOpen, ExternalLink, Target, TrendingUp } from 'lucide-react';
import Card from '../../ui/Card';
import Badge from '../../ui/Badge';
import Button from '../../ui/Button';
import CitationModal from '../../plan-engine/CitationModal';

interface KnowledgeInsight {
  kb_id: string;
  title: string;
  content: string;
  relevance_score: number;
  category: string;
  actionable_takeaway: string;
  user_context: string;
}

interface KnowledgeInsightsProps {
  analysis?: any;
  className?: string;
}

export const KnowledgeInsights: React.FC<KnowledgeInsightsProps> = ({ 
  analysis, 
  className = '' 
}) => {
  const [insights, setInsights] = useState<KnowledgeInsight[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedInsight, setSelectedInsight] = useState<string | null>(null);
  const [showCitationModal, setShowCitationModal] = useState(false);
  const [currentCitation, setCurrentCitation] = useState<string | null>(null);

  useEffect(() => {
    if (analysis) {
      fetchContextualInsights();
    }
  }, [analysis]);

  const fetchContextualInsights = async () => {
    setLoading(true);
    try {
      // Generate search queries based on user's analysis
      const searchQueries = generateSearchQueries(analysis);
      
      // For now, simulate insights based on the analysis using actual KB document IDs
      const mockInsights: KnowledgeInsight[] = [
        {
          kb_id: "PLAYBOOKS-922",
          title: "Retirement Planning Strategy",
          content: "Comprehensive retirement planning including 401(k) optimization, asset allocation by age, and catch-up contributions for 50+ individuals.",
          relevance_score: 0.95,
          category: "Investment Strategy",
          actionable_takeaway: "Review your current allocation and consider rebalancing",
          user_context: `Based on your ${formatCurrency(analysis.gaps?.current_trajectory || 0)} current portfolio`
        },
        {
          kb_id: "RESEARCH-808", 
          title: "Portfolio Optimization Research",
          content: "Modern portfolio theory applications including risk-return optimization and factor-based investing for current market conditions.",
          relevance_score: 0.88,
          category: "Investment Research",
          actionable_takeaway: "Consider portfolio optimization based on modern research",
          user_context: `With ${(analysis.gaps?.monthly_shortfall || 0) > 0 ? 'funding gap' : 'surplus'} monthly cash flow`
        },
        {
          kb_id: "REGULATIONS-59f", 
          title: "Fiduciary Duty Guidelines",
          content: "Comprehensive guidelines on fiduciary responsibilities, including best interest standards and disclosure requirements for financial advisors.",
          relevance_score: 0.82,
          category: "Regulatory Compliance",
          actionable_takeaway: "Ensure all recommendations meet fiduciary standards",
          user_context: "Professional guidance backed by regulatory requirements"
        }
      ];

      setInsights(mockInsights);
    } catch (error) {
      console.error('Failed to fetch contextual insights:', error);
      setInsights([]);
    } finally {
      setLoading(false);
    }
  };

  const generateSearchQueries = (analysis: any): string[] => {
    const queries = [];
    
    if (analysis?.goals?.some((g: any) => g.category === 'retirement')) {
      queries.push('retirement planning asset allocation');
    }
    
    if (analysis?.gaps?.monthly_shortfall > 0) {
      queries.push('cash flow optimization');
    }
    
    queries.push('tax optimization', 'portfolio rebalancing');
    return queries;
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'investment strategy':
        return <TrendingUp className="w-4 h-4" />;
      case 'tax planning':
        return <Target className="w-4 h-4" />;
      default:
        return <BookOpen className="w-4 h-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'investment strategy':
        return 'bg-blue-500';
      case 'tax planning':
        return 'bg-green-500';
      case 'regulatory guidance':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const handleViewKnowledge = (kbId: string) => {
    setCurrentCitation(kbId);
    setShowCitationModal(true);
  };

  const handleCloseCitation = () => {
    setShowCitationModal(false);
    setCurrentCitation(null);
  };

  if (loading) {
    return (
      <Card className={`border-blue-600 ${className}`}>
        <Card.Body className="p-6">
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-300">Loading insights...</span>
          </div>
        </Card.Body>
      </Card>
    );
  }

  return (
    <>
      <Card className={`border-blue-600 hover:border-blue-500 transition-colors ${className}`}>
        <Card.Body className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <BookOpen className="w-6 h-6 text-blue-400" />
              <h3 className="text-xl font-semibold text-white">Professional Insights</h3>
            </div>
            <Badge variant="outline" className="text-blue-400 border-blue-600">
              {insights.length} Insights
            </Badge>
          </div>

        <div className="space-y-4">
          {insights.map((insight, index) => (
            <div 
              key={insight.kb_id} 
              className="border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-3 h-3 rounded-full ${getCategoryColor(insight.category)}`}></div>
                    <span className="text-sm font-medium text-blue-400">{insight.kb_id}</span>
                    <Badge size="sm" className="text-xs">
                      {insight.category}
                    </Badge>
                  </div>
                  
                  <h4 className="font-semibold text-white mb-2">{insight.title}</h4>
                  <p className="text-gray-300 text-sm mb-3">{insight.content}</p>
                  
                  <div className="bg-blue-900/20 border-l-4 border-blue-500 p-3 mb-3">
                    <p className="text-blue-100 text-sm font-medium">
                      💡 {insight.actionable_takeaway}
                    </p>
                    <p className="text-blue-200 text-xs mt-1">
                      {insight.user_context}
                    </p>
                  </div>
                </div>
                
                <div className="flex flex-col gap-2 ml-4">
                  <div className="text-right">
                    <div className="text-xs text-gray-400">Relevance</div>
                    <div className="text-sm font-bold text-green-400">
                      {Math.round(insight.relevance_score * 100)}%
                    </div>
                  </div>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleViewKnowledge(insight.kb_id)}
                    className="text-xs"
                  >
                    <ExternalLink className="w-3 h-3 mr-1" />
                    View
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {insights.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-400">
            <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No contextual insights available</p>
            <p className="text-sm">Complete your financial analysis to see personalized recommendations</p>
          </div>
        )}

        <div className="mt-6 pt-4 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-400">
              Insights powered by professional knowledge base
            </p>
            <Button 
              size="sm" 
              variant="outline" 
              className="text-xs"
              onClick={() => {
                // Navigate to Step 5 where the full knowledge base is accessible
                window.location.href = '/advisory';
              }}
            >
              View All Knowledge →
            </Button>
          </div>
        </div>
      </Card.Body>
    </Card>

    {/* Citation Modal */}
    {showCitationModal && currentCitation && (
      <CitationModal
        citationId={currentCitation}
        onClose={handleCloseCitation}
      />
    )}
    </>
  );
};

export default KnowledgeInsights;