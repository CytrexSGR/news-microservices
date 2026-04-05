import { CheckCircle2, XCircle } from 'lucide-react';
import type { IndicatorsSnapshot } from '@/types/indicators';

interface TrendRegimeDisplayProps {
  liveIndicators: IndicatorsSnapshot;
  selectedTimeframe: string;
}

export function TrendRegimeDisplay({ liveIndicators, selectedTimeframe }: TrendRegimeDisplayProps) {
  if (!liveIndicators.regime_details) return null;

  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-xs font-semibold mb-2">
        Conditions ({liveIndicators.regime_details.conditions_met}/{liveIndicators.regime_details.conditions_total}):
      </p>

      {/* ADX Condition */}
      <div className={`p-2 rounded text-xs ${
        liveIndicators.regime_details.conditions.adx
          ? 'bg-green-500/10 border border-green-500/20'
          : 'bg-red-500/10 border border-red-500/20'
      }`}>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground font-medium">ADX &gt; 25:</span>
          {liveIndicators.regime_details.conditions.adx ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <XCircle className="h-3.5 w-3.5 text-red-500" />
          )}
        </div>
        <div className="mt-1 font-mono text-xs">
          <span className={liveIndicators.regime_details.conditions.adx ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
            ADX: {liveIndicators.regime_details.indicator_values.adx.toFixed(2)}
          </span>
        </div>
      </div>

      {/* DI Direction Condition */}
      <div className={`p-2 rounded text-xs ${
        liveIndicators.regime_details.conditions.di_direction
          ? 'bg-green-500/10 border border-green-500/20'
          : 'bg-red-500/10 border border-red-500/20'
      }`}>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground font-medium">DI Direction:</span>
          {liveIndicators.regime_details.conditions.di_direction ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <XCircle className="h-3.5 w-3.5 text-red-500" />
          )}
        </div>
        <div className="mt-1 font-mono text-xs">
          <span className={liveIndicators.regime_details.conditions.di_direction ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
            {liveIndicators.regime_details.indicator_values.di_direction}
          </span>
        </div>
      </div>

      {/* EMA Hierarchy Condition */}
      <div className={`p-2 rounded text-xs ${
        liveIndicators.regime_details.conditions.ema_hierarchy
          ? 'bg-green-500/10 border border-green-500/20'
          : 'bg-red-500/10 border border-red-500/20'
      }`}>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground font-medium">EMA Hierarchy:</span>
          {liveIndicators.regime_details.conditions.ema_hierarchy ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <XCircle className="h-3.5 w-3.5 text-red-500" />
          )}
        </div>
        <div className="mt-1 text-xs">
          <span className={liveIndicators.regime_details.conditions.ema_hierarchy ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
            {liveIndicators.regime_details.indicator_values.ema_hierarchy_valid ? 'Valid' : 'Invalid'}
          </span>
        </div>
      </div>

      {/* Volume Condition */}
      <div className={`p-2 rounded text-xs ${
        liveIndicators.regime_details.conditions.volume
          ? 'bg-green-500/10 border border-green-500/20'
          : 'bg-red-500/10 border border-red-500/20'
      }`}>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground font-medium">Volume &gt; 2x Avg:</span>
          {liveIndicators.regime_details.conditions.volume ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <XCircle className="h-3.5 w-3.5 text-red-500" />
          )}
        </div>
        <div className="mt-1 font-mono text-xs">
          <span className={liveIndicators.regime_details.conditions.volume ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
            {liveIndicators.regime_details.indicator_values.volume_ratio.toFixed(2)}x
          </span>
        </div>
      </div>

      {/* ATR Condition */}
      <div className={`p-2 rounded text-xs ${
        liveIndicators.regime_details.conditions.atr
          ? 'bg-green-500/10 border border-green-500/20'
          : 'bg-red-500/10 border border-red-500/20'
      }`}>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground font-medium">ATR &gt; Avg:</span>
          {liveIndicators.regime_details.conditions.atr ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <XCircle className="h-3.5 w-3.5 text-red-500" />
          )}
        </div>
        <div className="mt-1 font-mono text-xs">
          <span className={liveIndicators.regime_details.conditions.atr ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
            {(liveIndicators.regime_details.indicator_values.atr_percentile * 100).toFixed(0)}th percentile
          </span>
        </div>
      </div>

      {/* BBW Condition */}
      <div className={`p-2 rounded text-xs ${
        liveIndicators.regime_details.conditions.bbw
          ? 'bg-green-500/10 border border-green-500/20'
          : 'bg-red-500/10 border border-red-500/20'
      }`}>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground font-medium">BBW &lt;= 0.05:</span>
          {liveIndicators.regime_details.conditions.bbw ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
          ) : (
            <XCircle className="h-3.5 w-3.5 text-red-500" />
          )}
        </div>
        <div className="mt-1 font-mono text-xs">
          <span className={liveIndicators.regime_details.conditions.bbw ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
            BBW: {liveIndicators.regime_details.indicator_values.bbw.toFixed(4)}
          </span>
        </div>
      </div>
    </div>
  );
}
