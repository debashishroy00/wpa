/**
 * Citation Modal Component
 * Shows full knowledge base document content
 */
import React, { useState, useEffect } from 'react';
import { X, ExternalLink, FileText, Calendar, Tag } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';

interface KnowledgeBaseDocument {
  kb_id: string;
  title: string;
  category: string;
  content: string;
  tags: string[];
  last_updated: string;
  file_path: string;
  related_documents: Array<{
    kb_id: string;
    title: string;
    score: number;
  }>;
}

interface CitationModalProps {
  citationId: string;
  onClose: () => void;
}

const CitationModal: React.FC<CitationModalProps> = ({ citationId, onClose }) => {
  const [document, setDocument] = useState<KnowledgeBaseDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        setLoading(true);
        setError(null);

        // Mock API call - in production this would call the actual API
        const response = await fetch(`/api/v1/advisory/knowledge-base/document/${citationId}`);
        
        if (!response.ok) {
          throw new Error('Document not found');
        }

        const data = await response.json();
        setDocument(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document');
        // For demo purposes, provide mock data
        setDocument(getMockDocument(citationId));
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [citationId]);

  const getMockDocument = (kbId: string): KnowledgeBaseDocument => {
    const mockDocuments: Record<string, KnowledgeBaseDocument> = {
      'AL-001': {
        kb_id: 'AL-001',
        title: 'Asset Location Strategy',
        category: 'playbooks',
        content: `# Asset Location Strategy

**KB-ID: AL-001**
**Category: Tax Optimization**
**Last Updated: 2024-12-16**

## Overview
Asset location (asset placement) refers to holding different types of investments in the most tax-efficient account types to maximize after-tax returns.

## Tax-Advantaged Account Priority

### Tax-Deferred Accounts (401k, Traditional IRA)
1. **Bonds and Fixed Income** - High priority
   - Corporate bonds, Treasury bonds, CDs
   - Bond funds and bond ETFs
   - REITs (Real Estate Investment Trusts)
   - Rationale: Interest income taxed as ordinary income

### Roth Accounts (Roth IRA, Roth 401k)
1. **High-Growth Potential Assets** - Highest priority
   - Small-cap growth stocks
   - International/emerging market funds
   - Individual growth stocks
   - Rationale: Tax-free growth compounds over time

### Taxable Accounts
1. **Tax-Efficient Assets** - Preferred placement
   - Total stock market index funds
   - Broad market ETFs (VTI, VTIAX)
   - Individual blue-chip stocks held long-term
   - Municipal bonds (for high earners)

## Quantified Benefits
**High Earner (24% bracket) with $500k portfolio:**
- Optimal asset location: ~$2,000-4,000 annual tax savings
- Bond interest in 401k vs taxable: $1,200 annual savings
- Foreign tax credit in taxable: $300-600 annual benefit

---
**Sources**: IRS Publication 590, Bogleheads Asset Location Guide, Morningstar Tax Research
**Compliance**: Educational content only, not personalized tax advice`,
        tags: ['asset-location', 'tax-optimization', 'portfolio-management'],
        last_updated: '2024-12-16',
        file_path: 'playbooks/asset_location.md',
        related_documents: [
          { kb_id: 'RB-001', title: 'Rebalancing Strategy', score: 0.85 },
          { kb_id: 'IRS-001', title: 'IRS Contribution Limits', score: 0.72 }
        ]
      },
      'RB-001': {
        kb_id: 'RB-001',
        title: 'Portfolio Rebalancing Strategy',
        category: 'playbooks',
        content: `# Portfolio Rebalancing Strategy

**KB-ID: RB-001**
**Category: Portfolio Management**

## Rebalancing Methods

### 1. Calendar Rebalancing
**Best Practice**: Semi-annual rebalancing on fixed dates (Jan 1, July 1)

### 2. Threshold Rebalancing
**Absolute Threshold**: Rebalance when allocation differs by fixed percentage
- 5% threshold: Rebalance if target 60% stocks becomes 55% or 65%

### 3. Hybrid Approach (Recommended)
- Time: Check quarterly, rebalance semi-annually
- Threshold: 5% absolute drift for major asset classes

## Cost-Benefit Analysis
**Rebalancing Benefit**
- Adds 0.1-0.4% annual return for typical portfolios
- Risk reduction benefit often exceeds return benefit`,
        tags: ['rebalancing', 'portfolio-management'],
        last_updated: '2024-12-16',
        file_path: 'playbooks/rebalancing_strategy.md',
        related_documents: [
          { kb_id: 'AL-001', title: 'Asset Location Strategy', score: 0.85 },
          { kb_id: 'AA-001', title: 'Asset Allocation Research', score: 0.78 }
        ]
      }
    };

    return mockDocuments[kbId] || {
      kb_id: kbId,
      title: 'Document Not Found',
      category: 'unknown',
      content: 'Document content not available.',
      tags: [],
      last_updated: '2024-12-16',
      file_path: 'unknown',
      related_documents: []
    };
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const formatContent = (content: string) => {
    // Basic markdown-like formatting for display
    return content
      .split('\n')
      .map((line, index) => {
        if (line.startsWith('# ')) {
          return (
            <h1 key={index} className="text-2xl font-bold text-white mt-6 mb-4">
              {line.substring(2)}
            </h1>
          );
        }
        if (line.startsWith('## ')) {
          return (
            <h2 key={index} className="text-xl font-semibold text-white mt-5 mb-3">
              {line.substring(3)}
            </h2>
          );
        }
        if (line.startsWith('### ')) {
          return (
            <h3 key={index} className="text-lg font-medium text-white mt-4 mb-2">
              {line.substring(4)}
            </h3>
          );
        }
        if (line.startsWith('**') && line.endsWith('**')) {
          return (
            <div key={index} className="text-sm text-gray-400 mb-2">
              {line.replace(/\*\*/g, '')}
            </div>
          );
        }
        if (line.startsWith('- ')) {
          return (
            <li key={index} className="text-gray-300 ml-4 mb-1">
              {line.substring(2)}
            </li>
          );
        }
        if (line.trim() === '') {
          return <div key={index} className="mb-2"></div>;
        }
        return (
          <p key={index} className="text-gray-300 mb-2 leading-relaxed">
            {line}
          </p>
        );
      });
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-gray-900 border border-gray-700 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-blue-500" />
            <div>
              <h2 className="text-xl font-semibold text-white">
                {loading ? 'Loading...' : document?.title || 'Document'}
              </h2>
              <p className="text-sm text-gray-400">
                Knowledge Base Citation: [{citationId}]
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex h-[calc(90vh-120px)]">
          {/* Main Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {loading && (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            )}

            {error && (
              <div className="text-center py-8">
                <p className="text-red-400 mb-4">{error}</p>
                <Button onClick={onClose}>Close</Button>
              </div>
            )}

            {document && !loading && (
              <div className="space-y-4">
                {/* Document metadata */}
                <Card className="bg-gray-800">
                  <Card.Body>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div className="flex items-center gap-2">
                        <Tag className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400">Category:</span>
                        <span className="text-white capitalize">{document.category}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400">Updated:</span>
                        <span className="text-white">{document.last_updated}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <ExternalLink className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400">Source:</span>
                        <span className="text-white">{document.file_path}</span>
                      </div>
                    </div>
                    
                    {document.tags.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-700">
                        <div className="flex flex-wrap gap-2">
                          {document.tags.map(tag => (
                            <span 
                              key={tag}
                              className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card.Body>
                </Card>

                {/* Document content */}
                <div className="prose prose-invert max-w-none">
                  {formatContent(document.content)}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar - Related Documents */}
          {document && document.related_documents.length > 0 && (
            <div className="w-80 border-l border-gray-700 p-6 bg-gray-800">
              <h3 className="text-lg font-semibold text-white mb-4">Related Documents</h3>
              <div className="space-y-3">
                {document.related_documents.map(related => (
                  <div 
                    key={related.kb_id}
                    className="p-3 bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-600 transition-colors"
                    onClick={() => {
                      // Would navigate to related document
                      console.log('Navigate to:', related.kb_id);
                    }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-white">
                        [{related.kb_id}]
                      </span>
                      <span className="text-xs text-gray-400">
                        {(related.score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <p className="text-sm text-gray-300">{related.title}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-700 bg-gray-800">
          <div className="text-sm text-gray-400">
            This document is part of the WealthPath AI knowledge base and serves as a citation source for advisory recommendations.
          </div>
          <div className="flex gap-3">
            <Button variant="outline" size="sm">
              <ExternalLink className="w-4 h-4 mr-2" />
              View Source
            </Button>
            <Button onClick={onClose} className="bg-blue-600 hover:bg-blue-700">
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CitationModal;