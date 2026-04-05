import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';

interface SentimentBadgeProps {
  type: 'standard' | 'finance' | 'geopolitical' | 'category';
  value: string | number;
  confidence?: number;
  showConfidence?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function SentimentBadge({
  type,
  value,
  confidence,
  showConfidence = true,
  size: _size = 'md',
}: SentimentBadgeProps) {
  const getSentimentColor = (sentiment: string) => {
    const upper = sentiment.toUpperCase();
    if (upper === 'POSITIVE' || upper === 'BULLISH') return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    if (upper === 'NEGATIVE' || upper === 'BEARISH') return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    if (upper === 'NEUTRAL') return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    if (upper === 'MIXED') return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'Geopolitics Security': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      'Politics Society': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      'Economy Markets': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      'Climate Environment Health': 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200',
      'Panorama': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      'Technology Science': 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200',
    };
    return colors[category] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const getFinanceIcon = (sentiment: string) => {
    const upper = sentiment.toUpperCase();
    if (upper === 'BULLISH') return <TrendingUp className="h-3 w-3" />;
    if (upper === 'BEARISH') return <TrendingDown className="h-3 w-3" />;
    return <Minus className="h-3 w-3" />;
  };

  const formatStabilityScore = (score: number) => {
    const formatted = score.toFixed(2);
    if (score > 0.3) return `Stable +${formatted}`;
    if (score < -0.3) return `Unstable ${formatted}`;
    return `Neutral ${formatted}`;
  };

  const getStabilityColor = (score: number) => {
    if (score > 0.3) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    if (score < -0.3) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
  };

  const renderBadgeContent = () => {
    switch (type) {
      case 'standard':
        return (
          <>
            <span className="font-medium">{value}</span>
            {showConfidence && confidence !== undefined && (
              <span className="ml-1 text-xs opacity-75">({(confidence * 100).toFixed(0)}%)</span>
            )}
          </>
        );

      case 'finance':
        return (
          <div className="flex items-center gap-1">
            {getFinanceIcon(value as string)}
            <span className="font-medium">{value}</span>
            {showConfidence && confidence !== undefined && (
              <span className="ml-1 text-xs opacity-75">({(confidence * 100).toFixed(0)}%)</span>
            )}
          </div>
        );

      case 'geopolitical':
        return (
          <div className="flex items-center gap-1">
            {(value as number) < -0.3 && <AlertTriangle className="h-3 w-3" />}
            <span className="font-medium">{formatStabilityScore(value as number)}</span>
          </div>
        );

      case 'category':
        return <span className="font-medium">{value}</span>;

      default:
        return <span>{value}</span>;
    }
  };

  const getClassName = () => {
    if (type === 'standard' || type === 'finance') {
      return getSentimentColor(value as string);
    }
    if (type === 'geopolitical') {
      return getStabilityColor(value as number);
    }
    if (type === 'category') {
      return getCategoryColor(value as string);
    }
    return '';
  };

  return (
    <Badge variant="outline" className={`${getClassName()} border-0`}>
      {renderBadgeContent()}
    </Badge>
  );
}
