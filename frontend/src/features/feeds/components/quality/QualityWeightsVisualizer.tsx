/**
 * QualityWeightsVisualizer Component
 *
 * Radar chart visualization showing Admiralty Code weight distribution.
 * Uses the existing useQualityWeights hook to display current configuration.
 */
import { useMemo } from 'react';
import { useQualityWeights, useValidateWeights } from '../../api/useQualityWeights';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  CheckCircle,
  Settings2,
  Scale,
} from 'lucide-react';

interface QualityWeightsVisualizerProps {
  className?: string;
  showValidation?: boolean;
}

// Weight category configurations
const categoryConfig: Record<string, { label: string; color: string; description: string }> = {
  credibility: {
    label: 'Credibility',
    color: 'rgb(59, 130, 246)', // blue-500
    description: 'Source reputation and reliability',
  },
  editorial: {
    label: 'Editorial',
    color: 'rgb(168, 85, 247)', // purple-500
    description: 'Editorial standards and fact-checking',
  },
  trust: {
    label: 'Trust',
    color: 'rgb(34, 197, 94)', // green-500
    description: 'Third-party trust ratings',
  },
  health: {
    label: 'Health',
    color: 'rgb(251, 146, 60)', // orange-400
    description: 'Feed fetch success rate and stability',
  },
};

export function QualityWeightsVisualizer({
  className,
  showValidation = true,
}: QualityWeightsVisualizerProps) {
  const { data: weights, isLoading, error } = useQualityWeights();
  const { data: validation } = useValidateWeights();

  // Process weights for visualization
  const processedWeights = useMemo(() => {
    if (!weights) return [];

    return weights.map((weight) => ({
      category: weight.category,
      weight: parseFloat(weight.weight),
      ...categoryConfig[weight.category],
    }));
  }, [weights]);

  // Calculate max weight for scaling
  const maxWeight = useMemo(() => {
    if (!processedWeights.length) return 0.5;
    return Math.max(...processedWeights.map((w) => w.weight), 0.5);
  }, [processedWeights]);

  // SVG dimensions and calculations
  const size = 200;
  const center = size / 2;
  const radius = size * 0.4;
  const numPoints = processedWeights.length || 4;

  // Generate polygon points for the radar chart
  const generatePolygonPoints = (weights: typeof processedWeights) => {
    if (!weights.length) return '';

    return weights
      .map((w, i) => {
        const angle = (Math.PI * 2 * i) / numPoints - Math.PI / 2;
        const normalizedWeight = w.weight / maxWeight;
        const x = center + Math.cos(angle) * radius * normalizedWeight;
        const y = center + Math.sin(angle) * radius * normalizedWeight;
        return `${x},${y}`;
      })
      .join(' ');
  };

  // Generate grid lines
  const generateGridPolygon = (level: number) => {
    const points = [];
    for (let i = 0; i < numPoints; i++) {
      const angle = (Math.PI * 2 * i) / numPoints - Math.PI / 2;
      const x = center + Math.cos(angle) * radius * level;
      const y = center + Math.sin(angle) * radius * level;
      points.push(`${x},${y}`);
    }
    return points.join(' ');
  };

  // Generate axis lines
  const generateAxisLine = (index: number) => {
    const angle = (Math.PI * 2 * index) / numPoints - Math.PI / 2;
    const x = center + Math.cos(angle) * radius;
    const y = center + Math.sin(angle) * radius;
    return { x1: center, y1: center, x2: x, y2: y };
  };

  if (error) {
    return (
      <Card className={cn('p-4', className)}>
        <div className="flex items-center gap-2 text-destructive">
          <AlertTriangle className="h-5 w-5" />
          <span className="text-sm">Failed to load weight configuration</span>
        </div>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={cn('p-4', className)}>
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn('p-4', className)}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Scale className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Quality Weight Distribution</h3>
      </div>

      {/* Radar Chart */}
      <div className="flex justify-center mb-4">
        <svg width={size} height={size} className="overflow-visible">
          {/* Grid circles */}
          {[0.25, 0.5, 0.75, 1].map((level) => (
            <polygon
              key={level}
              points={generateGridPolygon(level)}
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              className="text-gray-200 dark:text-gray-700"
            />
          ))}

          {/* Axis lines */}
          {processedWeights.map((_, index) => {
            const line = generateAxisLine(index);
            return (
              <line
                key={index}
                {...line}
                stroke="currentColor"
                strokeWidth="1"
                className="text-gray-300 dark:text-gray-600"
              />
            );
          })}

          {/* Data polygon */}
          <polygon
            points={generatePolygonPoints(processedWeights)}
            fill="url(#gradient)"
            fillOpacity="0.3"
            stroke="url(#gradient)"
            strokeWidth="2"
          />

          {/* Data points */}
          {processedWeights.map((w, i) => {
            const angle = (Math.PI * 2 * i) / numPoints - Math.PI / 2;
            const normalizedWeight = w.weight / maxWeight;
            const x = center + Math.cos(angle) * radius * normalizedWeight;
            const y = center + Math.sin(angle) * radius * normalizedWeight;
            return (
              <circle
                key={w.category}
                cx={x}
                cy={y}
                r="4"
                fill={w.color}
                className="drop-shadow-sm"
              />
            );
          })}

          {/* Labels */}
          {processedWeights.map((w, i) => {
            const angle = (Math.PI * 2 * i) / numPoints - Math.PI / 2;
            const labelRadius = radius + 25;
            const x = center + Math.cos(angle) * labelRadius;
            const y = center + Math.sin(angle) * labelRadius;
            return (
              <text
                key={`label-${w.category}`}
                x={x}
                y={y}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-xs fill-current text-muted-foreground"
              >
                {w.label}
              </text>
            );
          })}

          {/* Gradient definition */}
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgb(59, 130, 246)" />
              <stop offset="50%" stopColor="rgb(168, 85, 247)" />
              <stop offset="100%" stopColor="rgb(34, 197, 94)" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      {/* Weight Details */}
      <div className="grid grid-cols-2 gap-2">
        {processedWeights.map((w) => (
          <div
            key={w.category}
            className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-gray-800/50"
          >
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: w.color }}
              />
              <span className="text-xs font-medium">{w.label}</span>
            </div>
            <span className="text-sm font-mono">{(w.weight * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>

      {/* Validation Status */}
      {showValidation && validation && (
        <div
          className={cn(
            'mt-4 p-2 rounded-lg flex items-center gap-2 text-sm',
            validation.is_valid
              ? 'bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-300'
              : 'bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300'
          )}
        >
          {validation.is_valid ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <AlertTriangle className="h-4 w-4" />
          )}
          <span>{validation.message}</span>
        </div>
      )}

      {/* Configuration Link */}
      <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Settings2 className="h-3 w-3" />
          <span>Configure weights in Admiralty Code settings</span>
        </div>
      </div>
    </Card>
  );
}
