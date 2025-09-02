/**
 * WealthPath AI - LLM Settings Service
 * Shared service for managing LLM provider settings across Step 5 and Step 6
 */

export interface ChatSettings {
    provider: 'openai' | 'gemini' | 'claude';
    modelTier: 'dev' | 'prod';
    selectedModel: string;
    estimatedCostPerMessage: number;
    temperature: number;
    insightLevel: 'direct' | 'balanced' | 'comprehensive';
}

export interface ModelConfig {
    model: string;
    costPer1k: {
        input: number;
        output: number;
    };
    icon: string;
    description: string;
}

const MODEL_CONFIGS = {
    openai: {
        dev: {
            model: 'gpt-3.5-turbo',
            costPer1k: { input: 0.001, output: 0.002 },
            icon: '⚡',
            description: 'Fastest'
        },
        prod: {
            model: 'gpt-4',
            costPer1k: { input: 0.03, output: 0.06 },
            icon: '⚡',
            description: 'Best Quality'
        }
    },
    gemini: {
        dev: {
            model: 'gemini-1.5-flash',
            costPer1k: { input: 0.001, output: 0.001 },
            icon: '💰',
            description: 'Cheapest'
        },
        prod: {
            model: 'gemini-1.5-pro',
            costPer1k: { input: 0.007, output: 0.007 },
            icon: '💰',
            description: 'Balanced'
        }
    },
    claude: {
        dev: {
            model: 'claude-3-haiku',
            costPer1k: { input: 0.003, output: 0.015 },
            icon: '🎯',
            description: 'Creative'
        },
        prod: {
            model: 'claude-3-opus',
            costPer1k: { input: 0.015, output: 0.075 },
            icon: '🎯',
            description: 'Best Quality'
        }
    }
} as const;

class LLMSettingsService {
    private static instance: LLMSettingsService;
    private settings: ChatSettings;
    private listeners: Array<(settings: ChatSettings) => void> = [];

    constructor() {
        // Load from localStorage or set defaults
        this.settings = this.loadSettings();
    }

    static getInstance(): LLMSettingsService {
        if (!this.instance) {
            this.instance = new LLMSettingsService();
        }
        return this.instance;
    }

    private loadSettings(): ChatSettings {
        try {
            const stored = localStorage.getItem('llm_settings');
            if (stored) {
                const parsed = JSON.parse(stored);
                return {
                    provider: parsed.provider || 'gemini',
                    modelTier: parsed.modelTier || 'dev',
                    selectedModel: this.getModelForProvider(parsed.provider || 'gemini', parsed.modelTier || 'dev'),
                    estimatedCostPerMessage: this.calculateMessageCost(2000, parsed.provider || 'gemini', parsed.modelTier || 'dev'),
                    temperature: parsed.temperature || 0.7,
                    insightLevel: parsed.insightLevel || 'balanced'
                };
            }
        } catch (error) {
            console.error('Failed to load LLM settings:', error);
        }

        // Default settings (cheapest option with balanced insights)
        return {
            provider: 'gemini',
            modelTier: 'dev',
            selectedModel: 'gemini-1.5-flash',
            estimatedCostPerMessage: 0.001,
            temperature: 0.7,
            insightLevel: 'balanced'
        };
    }

    getSettings(): ChatSettings {
        return { ...this.settings };
    }

    updateSettings(newSettings: Partial<ChatSettings>): void {
        this.settings = {
            ...this.settings,
            ...newSettings,
            selectedModel: this.getModelForProvider(
                newSettings.provider || this.settings.provider, 
                newSettings.modelTier || this.settings.modelTier
            ),
            estimatedCostPerMessage: this.calculateMessageCost(
                2000, 
                newSettings.provider || this.settings.provider, 
                newSettings.modelTier || this.settings.modelTier
            )
        };

        // Persist to localStorage
        localStorage.setItem('llm_settings', JSON.stringify(this.settings));

        // Notify listeners
        this.listeners.forEach(listener => listener(this.settings));
    }

    onSettingsChange(callback: (settings: ChatSettings) => void): () => void {
        this.listeners.push(callback);
        
        // Return unsubscribe function
        return () => {
            this.listeners = this.listeners.filter(listener => listener !== callback);
        };
    }

    getModelForProvider(provider: string, tier: string): string {
        return MODEL_CONFIGS[provider as keyof typeof MODEL_CONFIGS]?.[tier as 'dev' | 'prod']?.model || 'gpt-3.5-turbo';
    }

    getModelConfig(provider: string, tier: string): ModelConfig {
        const config = MODEL_CONFIGS[provider as keyof typeof MODEL_CONFIGS]?.[tier as 'dev' | 'prod'];
        if (!config) {
            return MODEL_CONFIGS.gemini.dev;
        }
        return config;
    }

    calculateMessageCost(tokens: number, provider: string, tier: string): number {
        const config = this.getModelConfig(provider, tier);
        // Assume 50% input tokens, 50% output tokens for estimation
        const inputTokens = Math.floor(tokens * 0.5);
        const outputTokens = Math.floor(tokens * 0.5);
        
        const inputCost = (inputTokens / 1000) * config.costPer1k.input;
        const outputCost = (outputTokens / 1000) * config.costPer1k.output;
        
        return parseFloat((inputCost + outputCost).toFixed(5));
    }

    getCostEstimate(provider: string, tier: string): string {
        return this.calculateMessageCost(2000, provider, tier).toFixed(3);
    }

    getProviderIcon(provider: string): string {
        const icons = {
            openai: '⚡',
            gemini: '💰', 
            claude: '🎯'
        };
        return icons[provider as keyof typeof icons] || '🤖';
    }

    getProviderDescription(provider: string, tier: string): string {
        return this.getModelConfig(provider, tier).description;
    }

    getProviderLabel(provider: string): string {
        const labels = {
            openai: 'Fastest',
            gemini: 'Cheapest',
            claude: 'Best Quality'
        };
        return labels[provider as keyof typeof labels] || provider.toUpperCase();
    }

    isCheapestOption(provider: string, tier: string): boolean {
        return provider === 'gemini' && tier === 'dev';
    }
}

export default LLMSettingsService.getInstance();