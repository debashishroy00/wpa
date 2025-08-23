/**
 * WealthPath AI - Intelligence Metrics Bar
 * Displays key financial metrics in a dashboard format
 */
import React from 'react';
import { TrendingDown, BarChart3, Shield, Heart } from 'lucide-react';
import Card from '../../ui/Card';

interface MetricsBarProps {
  monthlyGap: number;
  successRate: number;
  riskAlign: number;
  lifestyleFit: number;
}

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(Math.abs(amount));
};

const MetricCard: React.FC<{
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ReactNode;
  color: 'red' | 'green' | 'blue' | 'purple';
  isNegative?: boolean;
}> = ({ title, value, subtitle, icon, color, isNegative = false }) => {
  const colorClasses = {
    red: 'from-red-900 to-red-800',
    green: 'from-green-900 to-green-800', 
    blue: 'from-blue-900 to-blue-800',
    purple: 'from-purple-900 to-purple-800'
  };

  const iconColorClasses = {
    red: 'text-red-400',
    green: 'text-green-400',
    blue: 'text-blue-400', 
    purple: 'text-purple-400'
  };

  const textColorClasses = {
    red: 'text-red-200',
    green: 'text-green-200',
    blue: 'text-blue-200',
    purple: 'text-purple-200'
  };

  return (
    <Card className={`bg-gradient-to-r ${colorClasses[color]}`}>
      <Card.Body className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className={`${textColorClasses[color]} text-sm font-medium`}>{title}</p>
            <p className={`text-white text-2xl font-bold ${isNegative ? 'text-red-300' : ''}`}>
              {typeof value === 'number' && value < 0 && title.includes('GAP') ? 
                `-${formatCurrency(value)}` : 
                typeof value === 'string' ? value : `${value}%`
              }
            </p>
          </div>
          <div className={`${iconColorClasses[color]}`}>
            {icon}
          </div>
        </div>
        <div className="mt-2">
          <p className={`${textColorClasses[color]} text-xs`}>{subtitle}</p>
        </div>
      </Card.Body>
    </Card>
  );
};

export const MetricsBar: React.FC<MetricsBarProps> = ({ 
  monthlyGap, 
  successRate, 
  riskAlign, 
  lifestyleFit 
}) => {
  const getGapStatus = (gap: number) => {
    if (gap <= 0) return { text: 'surplus', color: 'green' as const };
    if (gap <= 5000) return { text: 'minor deficit', color: 'blue' as const };
    if (gap <= 15000) return { text: 'deficit', color: 'purple' as const };
    return { text: 'major deficit', color: 'red' as const };
  };

  const gapStatus = getGapStatus(monthlyGap);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Monthly Gap */}
      <MetricCard
        title="MONTHLY GAP"
        value={monthlyGap <= 0 ? formatCurrency(monthlyGap) : formatCurrency(monthlyGap)}
        subtitle={monthlyGap <= 0 ? 'surplus' : gapStatus.text}
        icon={<TrendingDown className="w-8 h-8" />}
        color={gapStatus.color}
        isNegative={monthlyGap > 0}
      />

      {/* Success Rate */}
      <MetricCard
        title="SUCCESS RATE"
        value={successRate}
        subtitle="probability"
        icon={<BarChart3 className="w-8 h-8" />}
        color={successRate >= 80 ? 'green' : successRate >= 60 ? 'blue' : 'red'}
      />

      {/* Risk Alignment */}
      <MetricCard
        title="RISK ALIGN"
        value={riskAlign}
        subtitle="matched"
        icon={<Shield className="w-8 h-8" />}
        color={riskAlign >= 85 ? 'green' : riskAlign >= 70 ? 'blue' : 'purple'}
      />

      {/* Lifestyle Fit */}
      <MetricCard
        title="LIFESTYLE FIT"
        value={lifestyleFit}
        subtitle="maintained"
        icon={<Heart className="w-8 h-8" />}
        color={lifestyleFit >= 90 ? 'green' : lifestyleFit >= 75 ? 'blue' : 'red'}
      />
    </div>
  );
};