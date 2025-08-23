/**
 * WealthPath AI - Suggested Questions Component
 * Contextual question suggestions based on user's financial situation
 */

import React, { useEffect, useState } from 'react';
import { MessageCircle, TrendingUp, Target, DollarSign, Home } from 'lucide-react';
import Card from '../ui/Card';

interface SuggestedQuestionsProps {
    onQuestionClick: (question: string) => void;
    disabled: boolean;
}

interface QuestionCategory {
    id: string;
    title: string;
    icon: React.ReactNode;
    questions: string[];
}

const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({
    onQuestionClick,
    disabled
}) => {
    const [selectedCategory, setSelectedCategory] = useState<string>('general');
    const [contextualQuestions, setContextualQuestions] = useState<string[]>([]);

    useEffect(() => {
        loadContextualQuestions();
    }, []);

    const loadContextualQuestions = async () => {
        try {
            // In a real implementation, this would call the backend
            // For now, we'll use static contextual questions based on the known user data
            const questions = generateContextualQuestions();
            setContextualQuestions(questions);
        } catch (error) {
            console.error('Failed to load contextual questions:', error);
        }
    };

    const generateContextualQuestions = (): string[] => {
        // Based on known user data: $2.56M net worth, 50.3% real estate, retirement goals, etc.
        return [
            "How can I reduce my 50.3% real estate concentration risk?",
            "Should I max out my retirement contributions with my $10,620 monthly surplus?",
            "What's the best tax strategy for my 24% federal tax bracket?",
            "How close am I to my $3.5M retirement goal?",
            "Should I rebalance my portfolio given my aggressive investment style?",
            "How can I optimize my $314K in liabilities?"
        ];
    };

    const questionCategories: QuestionCategory[] = [
        {
            id: 'contextual',
            title: 'Personalized',
            icon: <Target className="w-4 h-4" />,
            questions: contextualQuestions
        },
        {
            id: 'general',
            title: 'General',
            icon: <MessageCircle className="w-4 h-4" />,
            questions: [
                "What's my current financial health score?",
                "How am I doing compared to others my age?",
                "What should I focus on next financially?",
                "Show me my complete financial picture",
                "What are my biggest financial risks?",
                "How can I optimize my savings rate?"
            ]
        },
        {
            id: 'investments',
            title: 'Investments',
            icon: <TrendingUp className="w-4 h-4" />,
            questions: [
                "Is my investment allocation optimal?",
                "Should I diversify my portfolio more?",
                "What's my expected investment return?",
                "How much risk am I taking?",
                "Should I invest in more international funds?",
                "When should I rebalance my portfolio?"
            ]
        },
        {
            id: 'goals',
            title: 'Goals',
            icon: <Target className="w-4 h-4" />,
            questions: [
                "Am I on track for my retirement goal?",
                "How much should I save monthly for college?",
                "What's my path to financial independence?",
                "How can I accelerate my goals?",
                "Should I adjust my target dates?",
                "What goals should I prioritize?"
            ]
        },
        {
            id: 'taxes',
            title: 'Tax Strategy',
            icon: <DollarSign className="w-4 h-4" />,
            questions: [
                "How can I reduce my tax burden?",
                "Should I do tax-loss harvesting?",
                "What's the best retirement account strategy?",
                "Are there tax-efficient investment options?",
                "Should I consider municipal bonds?",
                "How can I optimize my withholdings?"
            ]
        },
        {
            id: 'real-estate',
            title: 'Real Estate',
            icon: <Home className="w-4 h-4" />,
            questions: [
                "Is my real estate allocation too high?",
                "Should I refinance my mortgage?",
                "Is now a good time to buy more property?",
                "How much house can I afford?",
                "Should I pay off my mortgage early?",
                "What's my rental property ROI?"
            ]
        }
    ];

    const currentQuestions = questionCategories.find(cat => cat.id === selectedCategory)?.questions || [];

    return (
        <Card className="bg-gray-800 border-gray-700 h-[600px] flex flex-col">
            <Card.Header>
                <Card.Title className="text-white flex items-center">
                    <MessageCircle className="w-5 h-5 mr-2 text-blue-400" />
                    Suggested Questions
                </Card.Title>
            </Card.Header>

            <Card.Body className="flex-1 overflow-hidden flex flex-col p-0">
                {/* Category Tabs */}
                <div className="border-b border-gray-700 p-3">
                    <div className="grid grid-cols-2 gap-1">
                        {questionCategories.map((category) => (
                            <button
                                key={category.id}
                                onClick={() => setSelectedCategory(category.id)}
                                disabled={disabled}
                                className={`p-2 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1 ${
                                    selectedCategory === category.id
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-700/50 text-gray-300 hover:bg-gray-700'
                                } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {category.icon}
                                <span className="truncate">{category.title}</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Questions List */}
                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    {currentQuestions.length === 0 ? (
                        <div className="text-center text-gray-500 mt-8">
                            <MessageCircle className="w-8 h-8 mx-auto mb-3 opacity-50" />
                            <p className="text-sm">Loading questions...</p>
                        </div>
                    ) : (
                        currentQuestions.map((question, index) => (
                            <button
                                key={index}
                                onClick={() => onQuestionClick(question)}
                                disabled={disabled}
                                className={`w-full text-left p-3 rounded-lg border transition-all ${
                                    disabled
                                        ? 'bg-gray-700/30 border-gray-600 text-gray-500 cursor-not-allowed'
                                        : 'bg-gray-700/50 border-gray-600 text-gray-300 hover:bg-gray-700 hover:border-gray-500 hover:text-white'
                                }`}
                            >
                                <div className="text-sm leading-relaxed">
                                    {question}
                                </div>
                                {selectedCategory === 'contextual' && (
                                    <div className="text-xs text-blue-400 mt-1">
                                        Personalized for you
                                    </div>
                                )}
                            </button>
                        ))
                    )}
                </div>

                {/* Category Info */}
                <div className="border-t border-gray-700 p-3">
                    <div className="text-xs text-gray-400 text-center">
                        {selectedCategory === 'contextual' ? (
                            <span className="flex items-center justify-center gap-1">
                                <Target className="w-3 h-3" />
                                Based on your financial profile
                            </span>
                        ) : (
                            <span>
                                {currentQuestions.length} questions available
                            </span>
                        )}
                    </div>
                </div>
            </Card.Body>
        </Card>
    );
};

export default SuggestedQuestions;