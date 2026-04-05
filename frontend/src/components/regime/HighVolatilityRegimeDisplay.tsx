import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { IndicatorsSnapshot } from '@/types/indicators';

interface HighVolatilityRegimeDisplayProps {
  liveIndicators: IndicatorsSnapshot;
  selectedTimeframe: string;
}

export function HighVolatilityRegimeDisplay({ liveIndicators, selectedTimeframe }: HighVolatilityRegimeDisplayProps) {
  if (!liveIndicators.regime_details?.high_volatility) return null;

  const hv = liveIndicators.regime_details.high_volatility;

  // Color coding for volatility type badge
  const volatilityTypeColor = hv.indicator_values.volatility_type === 'directional'
    ? 'default'
    : hv.indicator_values.volatility_type === 'chaotic'
    ? 'destructive'
    : 'secondary';

  return (
    <>
      {/* Live Indicators */}
      <div className="mt-3 p-3 bg-red-500/5 rounded-lg space-y-2">
        <p className="text-xs font-semibold mb-2">Live Indicators ({selectedTimeframe}):</p>
        <div className="space-y-1">
          {/* ATR */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">ATR:</span>
            <span className="font-mono font-medium">
              {hv.indicator_values.atr.toFixed(2)}
            </span>
          </div>

          {/* ATR Percentile */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">ATR Percentile:</span>
            <span className={`font-mono font-medium ${
              hv.indicator_values.atr_percentile >= 0.8
                ? 'text-red-600 dark:text-red-400'
                : 'text-green-600 dark:text-green-400'
            }`}>
              {(hv.indicator_values.atr_percentile * 100).toFixed(0)}%
            </span>
          </div>

          {/* ATR % of Price */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">ATR % of Price:</span>
            <span className="font-mono font-medium">
              {(hv.indicator_values.atr_pct * 100).toFixed(2)}%
            </span>
          </div>

          {/* BBW */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">BBW:</span>
            <span className={`font-mono font-medium ${
              hv.indicator_values.bbw > hv.indicator_values.bbw_threshold
                ? 'text-red-600 dark:text-red-400'
                : 'text-green-600 dark:text-green-400'
            }`}>
              {(hv.indicator_values.bbw * 100).toFixed(2)}%
            </span>
          </div>

          {/* BBW Threshold */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">BBW Threshold:</span>
            <span className="font-mono font-medium">
              {(hv.indicator_values.bbw_threshold * 100).toFixed(2)}%
            </span>
          </div>

          {/* ADX */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">ADX:</span>
            <span className="font-mono font-medium">
              {hv.indicator_values.adx.toFixed(2)}
            </span>
          </div>

          {/* Volatility Type */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Volatility Type:</span>
            <Badge variant={volatilityTypeColor} className="text-xs">
              {hv.indicator_values.volatility_type.toUpperCase()}
            </Badge>
          </div>
        </div>
      </div>

      {/* Conditions */}
      <div className="mt-3 space-y-1.5">
        <p className="text-xs font-semibold mb-2">
          Conditions ({hv.conditions_met}/{hv.conditions_total}):
        </p>

        {/* ATR High Condition */}
        <div className={`p-2 rounded text-xs ${
          hv.conditions.atr_high
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">ATR High (&gt;=80th percentile):</span>
            {hv.conditions.atr_high ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={hv.conditions.atr_high ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              {(hv.indicator_values.atr_percentile * 100).toFixed(0)}th percentile
            </span>
          </div>
        </div>

        {/* BBW High Condition */}
        <div className={`p-2 rounded text-xs ${
          hv.conditions.bbw_high
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">BBW High (&gt;{(hv.indicator_values.bbw_threshold * 100).toFixed(0)}%):</span>
            {hv.conditions.bbw_high ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={hv.conditions.bbw_high ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              BBW: {(hv.indicator_values.bbw * 100).toFixed(2)}%
            </span>
          </div>
        </div>

        {/* ADX Context (Informational) */}
        <div className="p-2 rounded text-xs bg-blue-500/10 border border-blue-500/20">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">ADX Context:</span>
            <Badge variant={volatilityTypeColor} className="text-xs">
              {hv.conditions.adx_context.toUpperCase()}
            </Badge>
          </div>
          <div className="mt-1 text-xs text-muted-foreground">
            {hv.conditions.adx_context === 'directional' && 'Strong trend with high volatility'}
            {hv.conditions.adx_context === 'chaotic' && 'High volatility without clear direction'}
            {hv.conditions.adx_context === 'mixed' && 'Moderate trend with volatility'}
          </div>
        </div>
      </div>

      {/* Risk Management Warnings */}
      <div className="mt-3 p-2 bg-orange-500/10 border border-orange-500/20 rounded">
        <p className="text-xs font-semibold text-orange-600 dark:text-orange-400 flex items-center gap-1">
          <AlertTriangle className="h-3.5 w-3.5" />
          Risk Management:
        </p>
        <ul className="text-xs text-orange-600/80 dark:text-orange-400/80 mt-1 space-y-0.5 ml-5 list-disc">
          <li>Reduce position size (50% or more)</li>
          <li>Widen stop-loss distances (1.5x-3.0x ATR)</li>
          <li>Consider breakout strategies OR pause trading</li>
          <li>Avoid range-bound strategies in directional volatility</li>
        </ul>
      </div>
    </>
  );
}
