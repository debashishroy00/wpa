/**
 * WealthPath AI - Generation Metadata Component
 * Display LLM response metadata including cost, timing, and validation
 */
import React, { useState } from 'react';
import { 
  Clock, 
  DollarSign, 
  Zap, 
  CheckCircle, 
  AlertTriangle, 
  Eye, 
  EyeOff,
  Hash,
  FileText,
  TrendingUp,
  Shield
} from 'lucide-react';

import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

interface NumberValidation {
  original_number: number;
  validated_number: number;
  is_valid: boolean;
  confidence_score: number;
  validation_method: string;
  error_message?: string;
}

interface Citation {
  doc_id: string;
  title: string;
  excerpt: string;
  relevance_score: number;
  page_number?: number;
  section?: string;
}

interface LLMResponse {
  provider: string;
  model: string;
  content: string;
  citations: Citation[];
  number_validations: NumberValidation[];
  token_usage: TokenUsage;
  cost: number;
  generation_time: number;
  metadata: {
    finish_reason?: string;
    model_tier?: string;
    temperature?: number;
    stop_reason?: string;
    safety_ratings?: Record<string, any>;
  };
  created_at: string;
}

interface GenerationMetadataProps {
  response: LLMResponse;
  showDetailed?: boolean;
  className?: string;
}

const GenerationMetadata: React.FC<GenerationMetadataProps> = ({
  response,
  showDetailed = false,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(showDetailed);
  const [activeTab, setActiveTab] = useState<'overview' | 'validation' | 'citations' | 'technical'>('overview');

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'openai':
        return <Zap className="w-4 h-4 text-green-400" />;
      case 'gemini':
        return <Zap className="w-4 h-4 text-blue-400" />;
      case 'claude':
        return <Zap className="w-4 h-4 text-purple-400" />;
      default:
        return <Zap className="w-4 h-4 text-gray-400" />;
    }
  };

  const getValidationSummary = () => {
    const total = response.number_validations.length;
    const valid = response.number_validations.filter(v => v.is_valid).length;
    const avgConfidence = total > 0 
      ? response.number_validations.reduce((sum, v) => sum + v.confidence_score, 0) / total
      : 0;

    return { total, valid, invalid: total - valid, avgConfidence };
  };

  const getQualityScore = () => {
    const validation = getValidationSummary();
    let score = 1.0;

    // Penalize for validation errors
    if (validation.total > 0) {
      score *= (validation.valid / validation.total);
    }

    // Penalize for low confidence
    score *= validation.avgConfidence;

    // Bonus for citations
    if (response.citations.length > 0) {
      score = Math.min(1.0, score + 0.1);
    }

    return score;
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  const formatCost = (cost: any) => {
    // Type safety: Handle null, undefined, or non-numeric values
    if (cost === null || cost === undefined) {
      return '$0.0000';
    }
    
    const numCost = Number(cost);
    if (isNaN(numCost)) {
      return '$0.0000';
    }
    
    // Format properly
    if (numCost < 0.001) return `$${(numCost * 1000).toFixed(3)}k`;
    return `$${numCost.toFixed(4)}`;
  };

  const validation = getValidationSummary();
  const qualityScore = getQualityScore();

  return (
    <Card className={`${className}`}>
      <Card.Header>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getProviderIcon(response.provider)}
            <div>
              <h4 className="text-sm font-medium text-white">Generation Metadata</h4>
              <p className="text-xs text-gray-400">{response.model}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Quality Score */}
            <Badge 
              variant={qualityScore >= 0.8 ? 'success' : qualityScore >= 0.6 ? 'warning' : 'error'}
              className="text-xs"
            >
              Quality: {Math.round(qualityScore * 100)}%
            </Badge>
            
            {/* Toggle Details */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-400 hover:text-white"
            >
              {isExpanded ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </Card.Header>

      <Card.Body>
        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Clock className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-sm font-mono text-white">{formatDuration(response.generation_time)}</div>
            <div className="text-xs text-gray-400">Time</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <DollarSign className="w-4 h-4 text-green-400" />
            </div>
            <div className="text-sm font-mono text-white">{formatCost(response.cost)}</div>
            <div className="text-xs text-gray-400">Cost</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Hash className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-sm font-mono text-white">{response.token_usage.total_tokens.toLocaleString()}</div>
            <div className="text-xs text-gray-400">Tokens</div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center mb-1">
              <Shield className="w-4 h-4 text-yellow-400" />
            </div>
            <div className="text-sm font-mono text-white">{validation.valid}/{validation.total}</div>
            <div className="text-xs text-gray-400">Validated</div>
          </div>
        </div>

        {/* Detailed View */}
        {isExpanded && (
          <>
            {/* Tab Navigation */}
            <div className="flex border-b border-gray-700 mb-4">
              {[
                { id: 'overview', label: 'Overview', icon: TrendingUp },
                { id: 'validation', label: 'Validation', icon: Shield },
                { id: 'citations', label: 'Citations', icon: FileText },
                { id: 'technical', label: 'Technical', icon: Zap }
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setActiveTab(id as any)}
                  className={`flex items-center space-x-2 px-4 py-2 text-sm transition-colors ${
                    activeTab === id
                      ? 'text-blue-400 border-b-2 border-blue-400'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="space-y-4">
              {activeTab === 'overview' && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h5 className="text-sm font-medium text-white mb-2">Token Breakdown</h5>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Input:</span>
                          <span className="text-white font-mono">{response.token_usage.input_tokens.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Output:</span>
                          <span className="text-white font-mono">{response.token_usage.output_tokens.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between border-t border-gray-700 pt-1">
                          <span className="text-gray-400">Total:</span>
                          <span className="text-white font-mono">{response.token_usage.total_tokens.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h5 className="text-sm font-medium text-white mb-2">Generation Info</h5>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-400">Provider:</span>
                          <span className="text-white">{response.provider}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Model:</span>
                          <span className="text-white font-mono text-xs">{response.model}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Tier:</span>
                          <span className="text-white">{response.metadata.model_tier || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-400">Temperature:</span>
                          <span className="text-white">{response.metadata.temperature || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'validation' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h5 className="text-sm font-medium text-white">Number Validation Results</h5>
                    <Badge 
                      variant={validation.invalid === 0 ? 'success' : 'warning'}
                      className="text-xs"
                    >
                      {validation.valid}/{validation.total} valid
                    </Badge>
                  </div>
                  
                  {response.number_validations.length === 0 ? (
                    <p className="text-sm text-gray-400">No numbers detected for validation</p>
                  ) : (
                    <div className="space-y-2">
                      {response.number_validations.map((validation, index) => (
                        <div 
                          key={index}
                          className={`p-3 rounded-lg border ${
                            validation.is_valid 
                              ? 'border-green-600 bg-green-600/10' 
                              : 'border-red-600 bg-red-600/10'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              {validation.is_valid ? (
                                <CheckCircle className="w-4 h-4 text-green-400" />
                              ) : (
                                <AlertTriangle className="w-4 h-4 text-red-400" />
                              )}
                              <span className="text-sm font-mono text-white">
                                {validation.original_number.toLocaleString()}
                              </span>
                            </div>
                            <Badge 
                              variant={validation.confidence_score >= 0.8 ? 'success' : 'warning'}
                              className="text-xs"
                            >
                              {Math.round(validation.confidence_score * 100)}%
                            </Badge>
                          </div>
                          
                          <div className="text-xs text-gray-400">
                            Method: {validation.validation_method}
                            {validation.error_message && (
                              <div className="text-red-400 mt-1">{validation.error_message}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'citations' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h5 className="text-sm font-medium text-white">Knowledge Base Citations</h5>
                    <Badge variant="secondary" className="text-xs">
                      {response.citations.length} sources
                    </Badge>
                  </div>
                  
                  {response.citations.length === 0 ? (
                    <p className="text-sm text-gray-400">No knowledge base sources cited</p>
                  ) : (
                    <div className="space-y-2">
                      {response.citations.map((citation, index) => (
                        <div key={index} className="p-3 bg-gray-800 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h6 className="text-sm font-medium text-white">{citation.title}</h6>
                            <Badge variant="secondary" className="text-xs">
                              {Math.round(citation.relevance_score * 100)}% relevant
                            </Badge>
                          </div>
                          <p className="text-xs text-gray-400 mb-2">{citation.excerpt}</p>
                          <div className="text-xs text-gray-500">
                            Doc ID: {citation.doc_id}
                            {citation.section && ` • Section: ${citation.section}`}
                            {citation.page_number && ` • Page: ${citation.page_number}`}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'technical' && (
                <div className="space-y-3">
                  <h5 className="text-sm font-medium text-white">Technical Details</h5>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h6 className="text-xs font-medium text-gray-300 mb-2">Response Metadata</h6>
                      <div className="bg-gray-800 rounded p-3 text-xs font-mono">
                        <div className="space-y-1">
                          {Object.entries(response.metadata).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="text-gray-400">{key}:</span>
                              <span className="text-white">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h6 className="text-xs font-medium text-gray-300 mb-2">Generation Details</h6>
                      <div className="bg-gray-800 rounded p-3 text-xs font-mono">
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Created:</span>
                            <span className="text-white">
                              {new Date(response.created_at).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Content Length:</span>
                            <span className="text-white">{response.content.length} chars</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">Tokens/Char:</span>
                            <span className="text-white">
                              {(response.token_usage.total_tokens / response.content.length).toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </Card.Body>
    </Card>
  );
};

export default GenerationMetadata;