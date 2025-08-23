/**
 * WealthPath AI - LLM Comparison View Component
 * Side-by-side comparison of multiple LLM provider responses
 */
import React, { useState, useMemo } from 'react';
import { 
  BarChart3, 
  Clock, 
  DollarSign, 
  Zap, 
  CheckCircle, 
  AlertTriangle,
  Trophy,
  Target,
  Hash,
  TrendingUp,
  Copy,
  Eye,
  EyeOff
} from 'lucide-react';

import Card from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import GenerationMetadata from './GenerationMetadata';

interface LLMResponse {
  provider: string;
  model: string;
  content: string;
  citations: any[];
  number_validations: any[];
  token_usage: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  cost: number;
  generation_time: number;
  metadata: any;
  created_at: string;
}

interface LLMComparison {
  request_id: string;
  responses: LLMResponse[];
  total_cost: number;
  fastest_provider: string;
  most_cost_effective: string;
  consensus_score: number;
  created_at: string;
}

interface LLMComparisonViewProps {
  comparison: LLMComparison;
  onSelectResponse?: (response: LLMResponse) => void;
  showMetadata?: boolean;
  className?: string;
}

const LLMComparisonView: React.FC<LLMComparisonViewProps> = ({
  comparison,
  onSelectResponse,
  showMetadata = true,
  className = ''
}) => {
  const [selectedResponse, setSelectedResponse] = useState<string | null>(null);
  const [showDetailedMetadata, setShowDetailedMetadata] = useState(false);
  const [copiedContent, setCopiedContent] = useState<string | null>(null);

  const providerColors = {
    openai: 'text-green-400 border-green-500',
    gemini: 'text-blue-400 border-blue-500',
    claude: 'text-purple-400 border-purple-500'
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'openai':
        return <Zap className="w-5 h-5 text-green-400" />;
      case 'gemini':
        return <Zap className="w-5 h-5 text-blue-400" />;
      case 'claude':
        return <Zap className="w-5 h-5 text-purple-400" />;
      default:
        return <Zap className="w-5 h-5 text-gray-400" />;
    }
  };

  const comparisonStats = useMemo(() => {
    const responses = comparison.responses;
    
    // Calculate validation scores
    const validationScores = responses.map(r => {
      const total = r.number_validations.length;
      const valid = r.number_validations.filter(v => v.is_valid).length;
      return total > 0 ? valid / total : 1; // 100% if no numbers to validate
    });

    // Calculate quality scores
    const qualityScores = responses.map((r, i) => {
      let score = validationScores[i];
      
      // Bonus for citations
      if (r.citations.length > 0) {
        score = Math.min(1.0, score + 0.1);
      }
      
      // Penalty for very short or very long responses
      const length = r.content.length;
      if (length < 200) score *= 0.8;
      if (length > 2000) score *= 0.9;
      
      return score;
    });

    // Find winners
    const fastestIndex = responses.findIndex(r => r.provider === comparison.fastest_provider);
    const cheapestIndex = responses.findIndex(r => r.provider === comparison.most_cost_effective);
    const highestQualityIndex = qualityScores.indexOf(Math.max(...qualityScores));

    return {
      validationScores,
      qualityScores,
      fastestIndex,
      cheapestIndex,
      highestQualityIndex,
      avgCost: responses.reduce((sum, r) => sum + r.cost, 0) / responses.length,
      avgTime: responses.reduce((sum, r) => sum + r.generation_time, 0) / responses.length,
      avgQuality: qualityScores.reduce((sum, s) => sum + s, 0) / qualityScores.length
    };
  }, [comparison]);

  const handleCopyContent = async (content: string, provider: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedContent(provider);
      setTimeout(() => setCopiedContent(null), 2000);
    } catch (err) {
      console.error('Failed to copy content:', err);
    }
  };

  const handleSelectResponse = (response: LLMResponse) => {
    setSelectedResponse(response.provider);
    onSelectResponse?.(response);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Comparison Header */}
      <Card>
        <Card.Header>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-6 h-6 text-blue-400" />
              <div>
                <h3 className="text-lg font-semibold text-white">LLM Provider Comparison</h3>
                <p className="text-sm text-gray-400">
                  Comparing {comparison.responses.length} providers • 
                  Consensus: {Math.round(comparison.consensus_score * 100)}%
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="text-xs">
                ID: {comparison.request_id}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowDetailedMetadata(!showDetailedMetadata)}
                className="text-gray-400 hover:text-white"
              >
                {showDetailedMetadata ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
          </div>
        </Card.Header>

        <Card.Body>
          {/* Overall Stats */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="text-center p-3 bg-gray-800 rounded-lg">
              <DollarSign className="w-5 h-5 text-green-400 mx-auto mb-2" />
              <div className="text-lg font-mono text-white">${comparison.total_cost.toFixed(4)}</div>
              <div className="text-xs text-gray-400">Total Cost</div>
            </div>
            
            <div className="text-center p-3 bg-gray-800 rounded-lg">
              <Clock className="w-5 h-5 text-blue-400 mx-auto mb-2" />
              <div className="text-lg font-mono text-white">{comparisonStats.avgTime.toFixed(2)}s</div>
              <div className="text-xs text-gray-400">Avg Time</div>
            </div>
            
            <div className="text-center p-3 bg-gray-800 rounded-lg">
              <Target className="w-5 h-5 text-purple-400 mx-auto mb-2" />
              <div className="text-lg font-mono text-white">{Math.round(comparisonStats.avgQuality * 100)}%</div>
              <div className="text-xs text-gray-400">Avg Quality</div>
            </div>
            
            <div className="text-center p-3 bg-gray-800 rounded-lg">
              <TrendingUp className="w-5 h-5 text-yellow-400 mx-auto mb-2" />
              <div className="text-lg font-mono text-white">{Math.round(comparison.consensus_score * 100)}%</div>
              <div className="text-xs text-gray-400">Consensus</div>
            </div>
          </div>

          {/* Winner Badges */}
          <div className="flex flex-wrap gap-2 mb-4">
            <Badge variant="success" className="flex items-center space-x-1">
              <Trophy className="w-3 h-3" />
              <span>Fastest: {comparison.fastest_provider}</span>
            </Badge>
            <Badge variant="success" className="flex items-center space-x-1">
              <DollarSign className="w-3 h-3" />
              <span>Cheapest: {comparison.most_cost_effective}</span>
            </Badge>
            <Badge variant="success" className="flex items-center space-x-1">
              <Target className="w-3 h-3" />
              <span>Highest Quality: {comparison.responses[comparisonStats.highestQualityIndex]?.provider}</span>
            </Badge>
          </div>
        </Card.Body>
      </Card>

      {/* Response Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {comparison.responses.map((response, index) => {
          const isSelected = selectedResponse === response.provider;
          const isFastest = comparisonStats.fastestIndex === index;
          const isCheapest = comparisonStats.cheapestIndex === index;
          const isHighestQuality = comparisonStats.highestQualityIndex === index;
          const validationScore = comparisonStats.validationScores[index];
          const qualityScore = comparisonStats.qualityScores[index];

          return (
            <Card 
              key={response.provider}
              className={`relative ${
                isSelected ? 'ring-2 ring-blue-500' : ''
              } ${providerColors[response.provider as keyof typeof providerColors]?.split(' ')[1] || 'border-gray-600'}`}
            >
              {/* Winner Badges */}
              <div className="absolute -top-2 -right-2 flex flex-col space-y-1">
                {isFastest && <Badge variant="success" className="text-xs">⚡ Fastest</Badge>}
                {isCheapest && <Badge variant="success" className="text-xs">💰 Cheapest</Badge>}
                {isHighestQuality && <Badge variant="success" className="text-xs">🏆 Best Quality</Badge>}
              </div>

              <Card.Header>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {getProviderIcon(response.provider)}
                    <div>
                      <h4 className="text-md font-semibold text-white capitalize">
                        {response.provider}
                      </h4>
                      <p className="text-xs text-gray-400 font-mono">{response.model}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleCopyContent(response.content, response.provider)}
                      className="text-gray-400 hover:text-white"
                    >
                      {copiedContent === response.provider ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                    
                    {onSelectResponse && (
                      <Button
                        variant={isSelected ? "primary" : "outline"}
                        size="sm"
                        onClick={() => handleSelectResponse(response)}
                      >
                        {isSelected ? 'Selected' : 'Select'}
                      </Button>
                    )}
                  </div>
                </div>
              </Card.Header>

              <Card.Body className="space-y-4">
                {/* Quick Stats */}
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="text-center">
                    <div className="font-mono text-white">{response.generation_time.toFixed(2)}s</div>
                    <div className="text-gray-400">Time</div>
                  </div>
                  <div className="text-center">
                    <div className="font-mono text-white">${response.cost.toFixed(4)}</div>
                    <div className="text-gray-400">Cost</div>
                  </div>
                  <div className="text-center">
                    <div className="font-mono text-white">{Math.round(qualityScore * 100)}%</div>
                    <div className="text-gray-400">Quality</div>
                  </div>
                </div>

                {/* Validation Status */}
                <div className="flex items-center justify-between p-2 bg-gray-800 rounded">
                  <div className="flex items-center space-x-2">
                    {validationScore === 1 ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-yellow-400" />
                    )}
                    <span className="text-xs text-gray-300">Number Validation</span>
                  </div>
                  <Badge 
                    variant={validationScore === 1 ? 'success' : 'warning'}
                    className="text-xs"
                  >
                    {Math.round(validationScore * 100)}%
                  </Badge>
                </div>

                {/* Content Preview */}
                <div className="space-y-2">
                  <h5 className="text-sm font-medium text-white">Response Preview</h5>
                  <div className="bg-gray-800 rounded p-3 max-h-40 overflow-y-auto">
                    <p className="text-sm text-gray-300 leading-relaxed">
                      {response.content.length > 300 
                        ? `${response.content.substring(0, 300)}...`
                        : response.content
                      }
                    </p>
                  </div>
                  <div className="text-xs text-gray-400">
                    {response.content.length} characters • {response.token_usage.total_tokens} tokens
                  </div>
                </div>

                {/* Token Usage Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-gray-400">
                    <span>Token Usage</span>
                    <span>{response.token_usage.total_tokens.toLocaleString()}</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full"
                      style={{
                        width: `${Math.min(100, (response.token_usage.total_tokens / 4000) * 100)}%`
                      }}
                    />
                  </div>
                </div>

                {/* Detailed Metadata */}
                {showDetailedMetadata && showMetadata && (
                  <GenerationMetadata 
                    response={response}
                    showDetailed={false}
                    className="mt-4"
                  />
                )}
              </Card.Body>
            </Card>
          );
        })}
      </div>

      {/* Detailed Analysis */}
      {showDetailedMetadata && (
        <Card>
          <Card.Header>
            <h4 className="text-lg font-semibold text-white">Detailed Analysis</h4>
          </Card.Header>
          <Card.Body>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Cost Analysis */}
              <div>
                <h5 className="text-md font-medium text-white mb-3">Cost Breakdown</h5>
                <div className="space-y-2">
                  {comparison.responses.map((response, index) => (
                    <div key={response.provider} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                      <div className="flex items-center space-x-2">
                        {getProviderIcon(response.provider)}
                        <span className="text-sm text-white capitalize">{response.provider}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-mono text-white">${response.cost.toFixed(4)}</div>
                        <div className="text-xs text-gray-400">
                          {Math.round((response.cost / comparison.total_cost) * 100)}% of total
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Performance Analysis */}
              <div>
                <h5 className="text-md font-medium text-white mb-3">Performance Metrics</h5>
                <div className="space-y-2">
                  {comparison.responses.map((response, index) => (
                    <div key={response.provider} className="flex items-center justify-between p-2 bg-gray-800 rounded">
                      <div className="flex items-center space-x-2">
                        {getProviderIcon(response.provider)}
                        <span className="text-sm text-white capitalize">{response.provider}</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-mono text-white">{response.generation_time.toFixed(2)}s</div>
                        <div className="text-xs text-gray-400">
                          Quality: {Math.round(comparisonStats.qualityScores[index] * 100)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default LLMComparisonView;