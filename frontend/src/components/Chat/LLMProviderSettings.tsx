/**
 * WealthPath AI - LLM Provider Settings Component
 * Reused from Step 5, adapted for Step 6 Chat interface
 */

import React from 'react';
import Card from '../ui/Card';
import LLMSettingsService from '../../services/LLMSettingsService';

const LLMProviderSettings: React.FC = () => {
    const settings = LLMSettingsService.getSettings();

    const handleProviderChange = (provider: 'openai' | 'gemini' | 'claude') => {
        LLMSettingsService.updateSettings({ provider });
    };

    const handleTierChange = (modelTier: 'dev' | 'prod') => {
        LLMSettingsService.updateSettings({ modelTier });
    };

    const handleInsightLevelChange = (insightLevel: 'direct' | 'balanced' | 'comprehensive') => {
        LLMSettingsService.updateSettings({ insightLevel });
    };

    return (
        <Card className="bg-gray-800/50 border-gray-700">
            <Card.Body className="p-4">
                <h3 className="text-base font-semibold text-white mb-3">🤖 LLM Provider Settings</h3>
                
                {/* Provider Selection */}
                <div className="mb-4">
                    <h4 className="text-white font-medium mb-2 text-sm">Choose Provider</h4>
                    <div className="grid grid-cols-3 gap-2">
                        {(['openai', 'gemini', 'claude'] as const).map(provider => (
                            <button
                                key={provider}
                                onClick={() => handleProviderChange(provider)}
                                className={`p-2 rounded border transition-all ${
                                    settings.provider === provider 
                                        ? 'bg-blue-900/30 border-blue-500 text-blue-300' 
                                        : 'bg-gray-700/30 border-gray-600 text-gray-300 hover:bg-gray-700/50'
                                }`}
                            >
                                <div className="text-center">
                                    <div className="text-lg mb-1">{LLMSettingsService.getProviderIcon(provider)}</div>
                                    <div className="font-medium text-sm">{provider.toUpperCase()}</div>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
                
                {/* Tier Selection */}
                <div className="mb-4">
                    <h4 className="text-white font-medium mb-2 text-sm">Model Tier</h4>
                    <div className="flex gap-2">
                        <button
                            onClick={() => handleTierChange('dev')}
                            className={`flex-1 p-2 rounded border transition-all ${
                                settings.modelTier === 'dev' 
                                    ? 'bg-green-900/30 border-green-500 text-green-300' 
                                    : 'bg-gray-700/30 border-gray-600 text-gray-300 hover:bg-gray-700/50'
                            }`}
                        >
                            <div className="text-center">
                                <div className="font-medium text-sm">💰 Dev</div>
                            </div>
                        </button>
                        <button
                            onClick={() => handleTierChange('prod')}
                            className={`flex-1 p-2 rounded border transition-all ${
                                settings.modelTier === 'prod' 
                                    ? 'bg-purple-900/30 border-purple-500 text-purple-300' 
                                    : 'bg-gray-700/30 border-gray-600 text-gray-300 hover:bg-gray-700/50'
                            }`}
                        >
                            <div className="text-center">
                                <div className="font-medium text-sm">🚀 Prod</div>
                            </div>
                        </button>
                    </div>
                </div>
                
                {/* Insight Level Selection */}
                <div className="mb-4">
                    <h4 className="text-white font-medium mb-2 text-sm">Response Depth</h4>
                    <div className="grid grid-cols-3 gap-2">
                        <button
                            onClick={() => handleInsightLevelChange('focused')}
                            className={`p-2 rounded border transition-all ${
                                settings.insightLevel === 'focused' 
                                    ? 'bg-blue-900/30 border-blue-500 text-blue-300' 
                                    : 'bg-gray-700/30 border-gray-600 text-gray-300 hover:bg-gray-700/50'
                            }`}
                        >
                            <div className="text-center">
                                <div className="text-lg mb-1">🎯</div>
                                <div className="font-medium text-sm">Focused</div>
                                <div className="text-xs opacity-60">Brief</div>
                            </div>
                        </button>
                        <button
                            onClick={() => handleInsightLevelChange('balanced')}
                            className={`p-2 rounded border transition-all ${
                                settings.insightLevel === 'balanced' 
                                    ? 'bg-blue-900/30 border-blue-500 text-blue-300' 
                                    : 'bg-gray-700/30 border-gray-600 text-gray-300 hover:bg-gray-700/50'
                            }`}
                        >
                            <div className="text-center">
                                <div className="text-lg mb-1">⚖️</div>
                                <div className="font-medium text-sm">Balanced</div>
                                <div className="text-xs opacity-60">Default</div>
                            </div>
                        </button>
                        <button
                            onClick={() => handleInsightLevelChange('comprehensive')}
                            className={`p-2 rounded border transition-all ${
                                settings.insightLevel === 'comprehensive' 
                                    ? 'bg-blue-900/30 border-blue-500 text-blue-300' 
                                    : 'bg-gray-700/30 border-gray-600 text-gray-300 hover:bg-gray-700/50'
                            }`}
                        >
                            <div className="text-center">
                                <div className="text-lg mb-1">📊</div>
                                <div className="font-medium text-sm">Comprehensive</div>
                                <div className="text-xs opacity-60">Full</div>
                            </div>
                        </button>
                    </div>
                </div>
                
                {/* Cost Display */}
                <div className="bg-yellow-900/20 border border-yellow-500/30 p-2 rounded text-center">
                    <div className="text-yellow-400 font-medium text-sm">
                        ${LLMSettingsService.getCostEstimate(settings.provider, settings.modelTier)} per message
                    </div>
                    <div className="text-yellow-300/70 text-xs">
                        {settings.provider.toUpperCase()} {settings.modelTier.toUpperCase()} • {
                            settings.insightLevel === 'focused' ? 'Brief answers (3-4 sentences)' :
                            settings.insightLevel === 'comprehensive' ? 'Detailed analysis with insights' :
                            'Balanced responses with context'
                        }
                        {LLMSettingsService.isCheapestOption(settings.provider, settings.modelTier) && (
                            <span className="ml-2 text-green-400">🎉 Cheapest</span>
                        )}
                    </div>
                </div>
            </Card.Body>
        </Card>
    );
};

export default LLMProviderSettings;