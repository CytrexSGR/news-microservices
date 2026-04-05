import { CheckCircle2, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { IndicatorsSnapshot } from '@/types/indicators';

interface ConsolidationRegimeDisplayProps {
  liveIndicators: IndicatorsSnapshot;
  selectedTimeframe: string;
}

export function ConsolidationRegimeDisplay({ liveIndicators, selectedTimeframe }: ConsolidationRegimeDisplayProps) {
  if (!liveIndicators.regime_details?.consolidation) return null;

  const consolidation = liveIndicators.regime_details.consolidation;

  return (
    <>
      {/* Live Indicators */}
      <div className="mt-3 p-3 bg-primary/5 rounded-lg space-y-2">
        <p className="text-xs font-semibold mb-2">Live Indicators ({selectedTimeframe}):</p>

        {/* ADX */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">ADX:</span>
          <span className="font-mono">{liveIndicators.adx?.adx?.toFixed(2) ?? 'N/A'}</span>
        </div>

        {/* RSI */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">RSI:</span>
          <span className="font-mono">{consolidation.indicator_values.rsi.toFixed(2)}</span>
        </div>

        {/* RSI Neutral Zone */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">RSI Neutral:</span>
          <Badge variant={consolidation.indicator_values.rsi_in_neutral_zone ? 'default' : 'destructive'}>
            {consolidation.indicator_values.rsi_in_neutral_zone ? 'YES' : 'NO'}
          </Badge>
        </div>

        {/* EMA Convergence */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">EMA Converged:</span>
          <Badge variant={consolidation.indicator_values.ema_converged ? 'default' : 'destructive'}>
            {consolidation.indicator_values.ema_converged ? 'YES' : 'NO'}
          </Badge>
        </div>

        {/* EMA Spread */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">EMA Spread:</span>
          <span className="font-mono">{consolidation.indicator_values.ema_spread_pct.toFixed(2)}%</span>
        </div>

        {/* Price Range */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">Range Width:</span>
          <span className="font-mono">{consolidation.indicator_values.range_width_pct.toFixed(2)}%</span>
        </div>

        {/* Volume Ratio */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">Volume Ratio:</span>
          <span className="font-mono">{consolidation.indicator_values.volume_ratio.toFixed(2)}x</span>
        </div>

        {/* ATR Percentile */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">ATR Percentile:</span>
          <span className="font-mono">{(consolidation.indicator_values.atr_percentile * 100).toFixed(0)}%</span>
        </div>

        {/* BBW Percentile */}
        <div className="flex justify-between text-xs">
          <span className="text-muted-foreground">BBW Percentile:</span>
          <span className="font-mono">{(consolidation.indicator_values.bbw_percentile * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Conditions Breakdown */}
      <div className="mt-3 space-y-1.5">
        <p className="text-xs font-semibold mb-2">
          Conditions ({consolidation.conditions_met}/{consolidation.conditions_total}):
        </p>

        {/* ADX Condition */}
        <div className={`p-2 rounded text-xs ${
          consolidation.conditions.adx
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">ADX ≤ 20:</span>
            {consolidation.conditions.adx ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={consolidation.conditions.adx ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              ADX: {liveIndicators.adx?.adx?.toFixed(2) ?? 'N/A'}
            </span>
          </div>
        </div>

        {/* RSI Neutral Condition */}
        <div className={`p-2 rounded text-xs ${
          consolidation.conditions.rsi_neutral
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">RSI Neutral (40-60):</span>
            {consolidation.conditions.rsi_neutral ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={consolidation.conditions.rsi_neutral ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              RSI: {consolidation.indicator_values.rsi.toFixed(2)}
            </span>
          </div>
        </div>

        {/* EMA Convergence Condition */}
        <div className={`p-2 rounded text-xs ${
          consolidation.conditions.ema_convergence
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">EMA Convergence:</span>
            {consolidation.conditions.ema_convergence ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={consolidation.conditions.ema_convergence ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              Spread: {consolidation.indicator_values.ema_spread_pct.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Price Range Condition */}
        <div className={`p-2 rounded text-xs ${
          consolidation.conditions.price_range
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">Tight Range (&lt; 5%):</span>
            {consolidation.conditions.price_range ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={consolidation.conditions.price_range ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              Range: {consolidation.indicator_values.range_width_pct.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Volume Low Condition */}
        <div className={`p-2 rounded text-xs ${
          consolidation.conditions.volume_low
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">Low Volume (&lt; 70%):</span>
            {consolidation.conditions.volume_low ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={consolidation.conditions.volume_low ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              Volume: {(consolidation.indicator_values.volume_ratio * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* ATR Low Condition */}
        <div className={`p-2 rounded text-xs ${
          consolidation.conditions.atr_low
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">Low ATR (≤ 30th):</span>
            {consolidation.conditions.atr_low ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={consolidation.conditions.atr_low ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              {(consolidation.indicator_values.atr_percentile * 100).toFixed(0)}th percentile
            </span>
          </div>
        </div>

        {/* BBW Squeeze Condition */}
        <div className={`p-2 rounded text-xs ${
          consolidation.conditions.bbw_squeeze
            ? 'bg-green-500/10 border border-green-500/20'
            : 'bg-red-500/10 border border-red-500/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground font-medium">BBW Squeeze:</span>
            {consolidation.conditions.bbw_squeeze ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <XCircle className="h-3.5 w-3.5 text-red-500" />
            )}
          </div>
          <div className="mt-1 font-mono text-xs">
            <span className={consolidation.conditions.bbw_squeeze ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              {(consolidation.indicator_values.bbw_percentile * 100).toFixed(0)}th percentile
              {consolidation.indicator_values.is_squeeze && ' (Squeeze)'}
            </span>
          </div>
        </div>
      </div>
    </>
  );
}
