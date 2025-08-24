/**
 * WealthPath AI - LLM Provider Selector Component
 * Multi-provider selection with cost optimization and real-time status
 */
import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  DollarSign, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Cpu,
  BarChart3,
  Settings
} from 'lucide-react';

import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import { apiClient } from '../../utils/api-simple';

interface LLMProvider {
  provider_id: string;
  name: string;
  is_enabled: boolean;
  models: {
    dev: {
      model: string;
      max_tokens: number;
      context_window: number;
    };
    prod: {
      model: string;
      max_tokens: number;
      context_window: number;
    };
  };
  cost_per_1k_input: number;
  cost_per_1k_output: number;
  client_status: 'connected' | 'not_configured';
}

interface ProvidersResponse {
  providers: Record<string, LLMProvider>;
  total_providers: number;
  available_providers: number;
}

interface LLMProviderSelectorProps {
  selectedProvider: string;
  onProviderChange: (provider: string) => void;
  selectedTier: 'dev' | 'prod';
  onTierChange: (tier: 'dev' | 'prod') => void;
  enableComparison?: boolean;
  onComparisonChange?: (enabled: boolean) => void;
  estimatedTokens?: number;
  className?: string;
}

const LLMProviderSelector: React.FC<LLMProviderSelectorProps> = ({
  selectedProvider,
  onProviderChange,
  selectedTier,
  onTierChange,
  enableComparison = false,
  onComparisonChange,
  estimatedTokens = 1000,
  className = ''
}) => {
  const [providers, setProviders] = useState<Record<string, LLMProvider>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    try {
      const data: ProvidersResponse = await apiClient.get('/api/v1/llm/providers');
      setProviders(data.providers);
      
      // Auto-select first available provider if none selected
      if (!selectedProvider) {
        const availableProviders = Object.entries(data.providers)
          .filter(([_, provider]) => provider.is_enabled)
          .map(([id, _]) => id);
        
        if (availableProviders.length > 0) {
          onProviderChange(availableProviders[0]);
        }
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load providers');
    } finally {
      setLoading(false);
    }
  };

  const calculateEstimatedCost = (provider: LLMProvider, tier: 'dev' | 'prod') => {
    const inputCost = (estimatedTokens / 1000) * provider.cost_per_1k_input;
    const outputCost = (estimatedTokens / 1000) * provider.cost_per_1k_output;
    return inputCost + outputCost;
  };

  const getProviderIcon = (providerId: string) => {
    switch (providerId) {
      case 'openai':
        return <Zap className="w-5 h-5 text-green-400" />;
      case 'gemini':
        return <Cpu className="w-5 h-5 text-blue-400" />;
      case 'claude':
        return <BarChart3 className="w-5 h-5 text-purple-400" />;
      default:
        return <Settings className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusIcon = (provider: LLMProvider) => {
    if (!provider.is_enabled || provider.client_status !== 'connected') {
      return <AlertCircle className="w-4 h-4 text-red-400" />;
    }
    return <CheckCircle className="w-4 h-4 text-green-400" />;
  };

  const getRecommendedProvider = () => {
    const availableProviders = Object.entries(providers)
      .filter(([_, provider]) => provider.is_enabled && provider.client_status === 'connected');
    
    if (availableProviders.length === 0) return null;
    
    // Recommend most cost-effective for dev tier
    if (selectedTier === 'dev') {
      return availableProviders.reduce((best, [id, provider]) => {
        const cost = calculateEstimatedCost(provider, 'dev');
        const bestCost = calculateEstimatedCost(best[1], 'dev');
        return cost < bestCost ? [id, provider] : best;
      })[0];
    }
    
    // Recommend best balance for prod tier (considering performance)
    return availableProviders[0][0]; // Simplified - could add performance metrics
  };

  if (loading) {
    return (
      <Card className={`${className}`}>
        <Card.Body>
          <div className="flex items-center justify-center h-20">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-300">Loading providers...</span>
          </div>
        </Card.Body>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`border-red-600 ${className}`}>
        <Card.Body>
          <div className="flex items-center text-red-400">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>{error}</span>
          </div>
        </Card.Body>
      </Card>
    );
  }

  const availableProviders = Object.entries(providers)
    .filter(([_, provider]) => provider.is_enabled && provider.client_status === 'connected');
  
  const recommendedProvider = getRecommendedProvider();

  return (
    <Card className={`${className}`}>
      <Card.Header>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">AI Provider Selection</h3>
          </div>
          <div className="flex items-center space-x-2">
            {/* Model Tier Selector */}
            <div className="flex rounded-lg bg-gray-700 p-1">
              <button
                onClick={() => onTierChange('dev')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  selectedTier === 'dev'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Dev
              </button>
              <button
                onClick={() => onTierChange('prod')}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  selectedTier === 'prod'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Prod
              </button>
            </div>
          </div>
        </div>
      </Card.Header>

      <Card.Body className="space-y-4">
        {/* Provider Selection */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {Object.entries(providers).map(([providerId, provider]) => {
            const isAvailable = provider.is_enabled && provider.client_status === 'connected';
            const isSelected = selectedProvider === providerId;
            const isRecommended = providerId === recommendedProvider;
            const estimatedCost = calculateEstimatedCost(provider, selectedTier);

            return (
              <div
                key={providerId}
                className={`relative p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  isSelected
                    ? 'border-blue-500 bg-blue-500/10'
                    : isAvailable
                    ? 'border-gray-600 hover:border-gray-500 bg-gray-800'
                    : 'border-gray-700 bg-gray-800/50 opacity-60 cursor-not-allowed'
                }`}
                onClick={() => isAvailable && onProviderChange(providerId)}
              >
                {/* Recommended Badge */}
                {isRecommended && isAvailable && (
                  <Badge 
                    variant="success" 
                    className="absolute -top-2 -right-2 text-xs"
                  >
                    Recommended
                  </Badge>
                )}

                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getProviderIcon(providerId)}
                    <span className="font-medium text-white">{provider.name}</span>
                  </div>
                  {getStatusIcon(provider)}
                </div>

                {/* Model Info */}
                <div className="text-sm text-gray-300 mb-2">
                  <div className="font-mono text-xs bg-gray-700 rounded px-2 py-1 mb-1">
                    {provider.models[selectedTier]?.model || 'N/A'}
                  </div>
                  <div className="text-xs text-gray-400">
                    Max tokens: {provider.models[selectedTier]?.max_tokens?.toLocaleString() || 'N/A'}
                  </div>
                </div>

                {/* Cost Estimate */}
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-1 text-gray-400">
                    <DollarSign className="w-3 h-3" />
                    <span>Est. cost</span>
                  </div>
                  <span className="font-mono text-green-400">
                    ${estimatedCost.toFixed(4)}
                  </span>
                </div>

                {/* Status */}
                <div className="mt-2 text-xs">
                  {!isAvailable && (
                    <span className="text-red-400">
                      {provider.client_status === 'not_configured' ? 'Not configured' : 'Disabled'}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Comparison Option */}
        {onComparisonChange && availableProviders.length > 1 && (
          <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-gray-300">Compare Multiple Providers</span>
              <Badge variant="secondary" className="text-xs">
                {availableProviders.length} available
              </Badge>
            </div>
            <button
              onClick={() => onComparisonChange(!enableComparison)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                enableComparison ? 'bg-blue-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  enableComparison ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        )}

        {/* Summary */}
        <div className="p-3 bg-gray-800 rounded-lg">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-gray-300">Available: {availableProviders.length}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-blue-400" />
              <span className="text-gray-300">Tier: {selectedTier.toUpperCase()}</span>
            </div>
          </div>
          
          {enableComparison && (
            <div className="mt-2 p-2 bg-purple-500/10 border border-purple-500/20 rounded text-xs text-purple-300">
              Comparison mode will generate responses from all available providers for analysis
            </div>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default LLMProviderSelector;