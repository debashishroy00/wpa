/**
 * WealthPath AI - Intelligence Score Card
 * Displays overall goal achievement score
 */
import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import Card from '../../ui/Card';

interface ScoreCardProps {
  score: number;
  trend: 'up' | 'down' | 'stable';
  message: string;
}

const CircularProgress: React.FC<{ value: number; size?: number }> = ({ value, size = 192 }) => {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = `${(value / 100) * circumference} ${circumference}`;
  
  const getColorClass = (value: number) => {
    if (value >= 80) return '#10b981'; // green-500
    if (value >= 60) return '#f59e0b'; // yellow-500
    if (value >= 40) return '#f97316'; // orange-500
    return '#ef4444'; // red-500
  };

  return (
    <div className="relative" style={{ width: size, height: size }}>
      {/* Background circle */}
      <svg className="absolute inset-0 w-full h-full" style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="8"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke={getColorClass(value)}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={strokeDasharray}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      
      {/* Score text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className={`text-4xl font-bold`} style={{ color: getColorClass(value) }}>
            {value}%
          </div>
          <div className="text-sm text-gray-400 mt-1">Achievement</div>
        </div>
      </div>
    </div>
  );
};

export const ScoreCard: React.FC<ScoreCardProps> = ({ score, trend, message }) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-5 h-5 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-5 h-5 text-red-500" />;
      default:
        return <Minus className="w-5 h-5 text-gray-400" />;
    }
  };

  const getTrendText = () => {
    switch (trend) {
      case 'up':
        return 'Improving trajectory';
      case 'down':
        return 'Needs attention';
      default:
        return 'Stable outlook';
    }
  };

  return (
    <Card className="bg-gradient-to-r from-gray-800 to-gray-700">
      <Card.Body className="p-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-6">Goal Achievement Score</h2>
          
          {/* Circular Progress */}
          <div className="flex justify-center mb-6">
            <CircularProgress value={score} />
          </div>
          
          {/* Message */}
          <p className="text-lg text-gray-300 mb-4">{message}</p>
          
          {/* Trend Indicator */}
          <div className="flex items-center justify-center gap-2">
            {getTrendIcon()}
            <span className="text-sm text-gray-400">{getTrendText()}</span>
          </div>
          
          {/* Score Interpretation */}
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="text-center">
              <div className="text-green-400 font-semibold">80-100%</div>
              <div className="text-gray-400">Excellent</div>
            </div>
            <div className="text-center">
              <div className="text-yellow-400 font-semibold">60-79%</div>
              <div className="text-gray-400">Good</div>
            </div>
            <div className="text-center">
              <div className="text-orange-400 font-semibold">40-59%</div>
              <div className="text-gray-400">Moderate</div>
            </div>
            <div className="text-center">
              <div className="text-red-400 font-semibold">0-39%</div>
              <div className="text-gray-400">Challenging</div>
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};