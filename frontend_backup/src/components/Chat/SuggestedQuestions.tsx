/**
 * WealthPath AI - Suggested Questions Component
 * Contextual question suggestions based on user's financial situation
 */

import React, { useEffect, useState } from 'react';
import { MessageCircle, TrendingUp, Target, DollarSign } from 'lucide-react';
import { QUESTION_SETS } from '../../content/question_sets';
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
    const [selectedCategory, setSelectedCategory] = useState<string>('retirement');

    useEffect(() => {}, []);

    // Build curated categories from QUESTION_SETS; map tile labels and prompts
    const questionCategories: QuestionCategory[] = QUESTION_SETS.map(cat => ({
        id: cat.id,
        title: cat.title,
        icon: cat.id === 'retirement' ? <Target className="w-4 h-4" />
             : cat.id === 'investing' ? <TrendingUp className="w-4 h-4" />
             : cat.id === 'taxes' ? <DollarSign className="w-4 h-4" />
             : <MessageCircle className="w-4 h-4" />,
        questions: cat.tiles.map(t => t.label)
    }));
    const labelToPromptMap: Record<string, string> = Object.fromEntries(
        QUESTION_SETS.flatMap(cat => cat.tiles.map(t => [t.label, t.prompt]))
    );

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
                                onClick={() => onQuestionClick(labelToPromptMap[question] || question)}
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
                        <span>{currentQuestions.length} questions available</span>
                    </div>
                </div>
            </Card.Body>
        </Card>
    );
};

export default SuggestedQuestions;
