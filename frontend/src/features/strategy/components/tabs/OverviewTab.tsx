/**
 * OverviewTab Component
 *
 * Displays the strategy overview including regime detection, entry/exit logic,
 * summary stats, and metadata.
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Activity,
  BarChart3,
  Target,
  Layers,
  Shield,
  Info,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import type { StrategyDefinition } from '../../types';
import type { IndicatorsSnapshot } from '@/types/indicators';
import type { StrategyEvaluationResponse, RegimeType, TradeDirection } from '@/types/strategy-evaluation';
import { TrendRegimeDisplay } from '@/components/regime/TrendRegimeDisplay';
import { ConsolidationRegimeDisplay } from '@/components/regime/ConsolidationRegimeDisplay';
import { HighVolatilityRegimeDisplay } from '@/components/regime/HighVolatilityRegimeDisplay';
import { EntryConditionsDisplay } from '@/components/strategy/EntryConditionsDisplay';
import { EntryScoreBar } from '@/components/strategy/EntryScoreBar';
import { ExitRulesDisplay } from '@/components/strategy/ExitRulesDisplay';
import { formatPrice } from '@/features/trading/utils/formatters';
import {
  getEntryEvaluation,
  getExitEvaluation,
  getAvailableDirections,
  DIRECTION_LABELS,
  DIRECTION_COLORS,
  DIRECTION_BG_COLORS,
  MARKET_DIRECTION_LABELS,
  DIRECTION_SIGNAL_LABELS,
  COMBINED_STATE_LABELS,
  getSignalStatusLabel,
  getSignalStatusColor,
  formatDirectionConfidence,
  getConfidenceColor,
  formatLeverage,
  formatLeverageRange,
  getLeverageColor,
  getLeverageBgColor,
  getLeverageRiskLabel,
} from '@/types/strategy-evaluation';

interface OverviewTabProps {
  definition: StrategyDefinition;
  selectedSymbol: string;
  selectedTimeframe: string;
  liveIndicators: IndicatorsSnapshot | null;
  strategyEvaluation: StrategyEvaluationResponse | null;
  evaluationLoading: boolean;
  evaluationError: Error | null;
}

export function OverviewTab({
  definition,
  selectedSymbol,
  selectedTimeframe,
  liveIndicators,
  strategyEvaluation,
  evaluationLoading,
  evaluationError,
}: OverviewTabProps) {
  const def = definition;

  return (
    <div className="space-y-4">
      {/* Regime Detection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Regime Detection
          </CardTitle>
          <CardDescription>How market regimes are detected</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2">Method</p>
            <Badge>
              {(def.regimeDetection as any).config?.method?.toUpperCase() || 'CUSTOM'}
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(
              (def.regimeDetection as any).config?.thresholds || {}
            ).map(([regime, config]: [string, any]) => {
              const isActive = liveIndicators?.regime === regime;

              return (
                <Card key={regime} className={isActive ? 'border-primary' : ''}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center justify-between">
                      {regime}
                      {isActive && (
                        <Badge variant="default" className="ml-2">
                          ACTIVE
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground mb-2">
                      {config.description}
                    </p>

                    {/* Live Indicators Display */}
                    {liveIndicators &&
                      regime === 'TREND' &&
                      liveIndicators.regime_details ? (
                      <TrendRegimeDisplay
                        liveIndicators={liveIndicators}
                        selectedTimeframe={selectedTimeframe}
                      />
                    ) : liveIndicators &&
                      regime === 'CONSOLIDATION' &&
                      liveIndicators.regime_details?.consolidation ? (
                      <ConsolidationRegimeDisplay
                        liveIndicators={liveIndicators}
                        selectedTimeframe={selectedTimeframe}
                      />
                    ) : liveIndicators &&
                      liveIndicators.regime_details?.high_volatility ? (
                      <HighVolatilityRegimeDisplay
                        liveIndicators={liveIndicators}
                        selectedTimeframe={selectedTimeframe}
                      />
                    ) : (
                      <ThresholdConditions
                        config={config}
                        liveIndicators={liveIndicators}
                      />
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2">
              Indicators Used
            </p>
            <div className="flex flex-wrap gap-2">
              {Object.values(
                (def.regimeDetection as any).config?.indicators || {}
              ).map((indicator: any, idx) => (
                <Badge key={idx} variant="secondary">
                  {String(indicator)}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Entry/Exit Logic Visualization */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Entry/Exit Logic
          </CardTitle>
          <CardDescription>
            Real-time evaluation of entry conditions and exit rules
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {evaluationLoading && (
            <div className="flex items-center justify-center py-8">
              <Activity className="h-6 w-6 animate-spin text-primary" />
              <span className="ml-2 text-sm text-muted-foreground">
                Loading strategy evaluation...
              </span>
            </div>
          )}

          {evaluationError && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Failed to load strategy evaluation: {evaluationError.message}
              </AlertDescription>
            </Alert>
          )}

          {strategyEvaluation && !evaluationLoading && (
            <EvaluationDisplay
              strategyEvaluation={strategyEvaluation}
              selectedSymbol={selectedSymbol}
            />
          )}
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Layers className="h-4 w-4" />
              Indicators
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{def.indicators.length}</p>
            <p className="text-xs text-muted-foreground">
              {def.indicators.filter((i) => i.timeframe === '1h').length} on 1h,{' '}
              {def.indicators.filter((i) => i.timeframe === '4h').length} on 4h,{' '}
              {def.indicators.filter((i) => i.timeframe === '1d').length} on 1d
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Target className="h-4 w-4" />
              Regimes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{Object.keys(def.logic).length}</p>
            <p className="text-xs text-muted-foreground">
              {
                Object.values(def.logic).filter(
                  (r: any) => r.entry_long || r.entry_short || r.entry
                ).length
              }{' '}
              active regimes
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Shield className="h-4 w-4" />
              Protections
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {(def.execution as any).protections?.length || 0}
            </p>
            <p className="text-xs text-muted-foreground">
              StoplossGuard, MaxDrawdown, etc.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Metadata */}
      {def.metadata && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              Metadata
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {(def.metadata as any).tags && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">Tags</p>
                <div className="flex flex-wrap gap-2">
                  {(def.metadata as any).tags.map((tag: string, idx: number) => (
                    <Badge key={idx} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {(def.metadata as any).targetMarkets && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  Target Markets
                </p>
                <div className="flex flex-wrap gap-2">
                  {(def.metadata as any).targetMarkets.map(
                    (market: string, idx: number) => (
                      <Badge key={idx} variant="secondary">
                        {market}
                      </Badge>
                    )
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============================================================================
// Helper Components
// ============================================================================

interface ThresholdConditionsProps {
  config: any;
  liveIndicators: IndicatorsSnapshot | null;
}

function ThresholdConditions({ config, liveIndicators }: ThresholdConditionsProps) {
  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-xs font-semibold mb-2">Threshold Conditions:</p>
      {Object.entries(config)
        .filter(([key]) => key !== 'description')
        .map(([key, value]) => {
          let currentValue: number | null = null;
          let conditionMet: boolean | null = null;
          let operator = '';
          let indicatorName = '';

          if (liveIndicators) {
            const adxValue = liveIndicators.adx?.adx;
            const bbwValue = liveIndicators.bollinger_bands?.width;

            if (key === 'adx_min' && adxValue !== undefined) {
              currentValue = adxValue;
              conditionMet = adxValue >= (value as number);
              operator = '>=';
              indicatorName = 'ADX';
            } else if (key === 'adx_max' && adxValue !== undefined) {
              currentValue = adxValue;
              conditionMet = adxValue <= (value as number);
              operator = '<=';
              indicatorName = 'ADX';
            } else if (key === 'bbw_min' && bbwValue !== undefined) {
              currentValue = bbwValue;
              conditionMet = bbwValue >= (value as number);
              operator = '>=';
              indicatorName = 'BBW';
            } else if (key === 'bbw_max' && bbwValue !== undefined) {
              currentValue = bbwValue;
              conditionMet = bbwValue <= (value as number);
              operator = '<=';
              indicatorName = 'BBW';
            }
          }

          return (
            <div
              key={key}
              className={`p-2 rounded text-xs ${
                conditionMet === true
                  ? 'bg-green-500/10 border border-green-500/20'
                  : conditionMet === false
                  ? 'bg-red-500/10 border border-red-500/20'
                  : 'bg-muted/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground font-medium">{key}:</span>
                {conditionMet !== null ? (
                  conditionMet ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5 text-red-500" />
                  )
                ) : null}
              </div>
              {currentValue !== null && (
                <div className="mt-1 font-mono text-xs">
                  <span
                    className={
                      conditionMet
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    }
                  >
                    {indicatorName}:{' '}
                    {currentValue.toFixed(indicatorName === 'BBW' ? 4 : 2)}
                  </span>
                  <span className="text-muted-foreground mx-1">{operator}</span>
                  <span className="text-foreground">{String(value)}</span>
                </div>
              )}
            </div>
          );
        })}
    </div>
  );
}

interface EvaluationDisplayProps {
  strategyEvaluation: StrategyEvaluationResponse;
  selectedSymbol: string;
}

function EvaluationDisplay({
  strategyEvaluation,
  selectedSymbol,
}: EvaluationDisplayProps) {
  return (
    <div className="space-y-6">
      {/* Current Price & Regime Banner */}
      <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Current Price */}
          <div>
            <p className="text-xs text-muted-foreground mb-1">
              Current Price ({selectedSymbol.replace('USDT', '/USDT')})
            </p>
            <p className="text-2xl font-bold font-mono">
              {formatPrice(strategyEvaluation.current_price)}
            </p>
          </div>

          {/* Active Regime */}
          <div>
            <p className="text-xs text-muted-foreground mb-1">Active Regime</p>
            <Badge
              variant={
                strategyEvaluation.current_regime === 'TREND'
                  ? 'default'
                  : strategyEvaluation.current_regime === 'HIGH_VOLATILITY'
                  ? 'destructive'
                  : 'secondary'
              }
              className="text-sm px-3 py-1"
            >
              {strategyEvaluation.current_regime.replace('_', ' ')}
            </Badge>
          </div>

          {/* Market Direction */}
          <div>
            <p className="text-xs text-muted-foreground mb-1">Market Direction</p>
            <div className="flex items-center gap-2">
              <Badge
                className={`text-sm px-3 py-1 ${
                  strategyEvaluation.current_direction === 'BULLISH'
                    ? 'bg-green-600 hover:bg-green-700'
                    : strategyEvaluation.current_direction === 'BEARISH'
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-yellow-600 hover:bg-yellow-700'
                }`}
              >
                {MARKET_DIRECTION_LABELS[strategyEvaluation.current_direction] ||
                  strategyEvaluation.current_direction}
              </Badge>
              <span
                className={`text-xs font-medium ${getConfidenceColor(
                  strategyEvaluation.direction_confidence
                )}`}
              >
                {formatDirectionConfidence(strategyEvaluation.direction_confidence)}
              </span>
            </div>
          </div>

          {/* Entry Allowed */}
          <div>
            <p className="text-xs text-muted-foreground mb-1">Entries Allowed</p>
            <div className="flex items-center gap-2">
              {strategyEvaluation.long_allowed && (
                <Badge className="bg-green-600 hover:bg-green-700 text-sm px-2 py-1">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Long
                </Badge>
              )}
              {strategyEvaluation.short_allowed && (
                <Badge className="bg-red-600 hover:bg-red-700 text-sm px-2 py-1">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Short
                </Badge>
              )}
              {!strategyEvaluation.long_allowed && !strategyEvaluation.short_allowed && (
                <Badge variant="secondary" className="text-sm px-2 py-1">
                  <XCircle className="h-3 w-3 mr-1" />
                  None
                </Badge>
              )}
            </div>
          </div>

          {/* Recommended Leverage */}
          {strategyEvaluation.recommended_leverage && (
            <div>
              <p className="text-xs text-muted-foreground mb-1">Recommended Leverage</p>
              <div className="flex items-center gap-2">
                <Badge
                  className={`text-sm px-3 py-1 ${getLeverageBgColor(
                    strategyEvaluation.recommended_leverage.value,
                    strategyEvaluation.recommended_leverage.max
                  )}`}
                >
                  <span
                    className={getLeverageColor(
                      strategyEvaluation.recommended_leverage.value,
                      strategyEvaluation.recommended_leverage.max
                    )}
                  >
                    {formatLeverage(strategyEvaluation.recommended_leverage.value)}
                  </span>
                </Badge>
                <span className="text-xs text-muted-foreground">
                  (
                  {formatLeverageRange(
                    strategyEvaluation.recommended_leverage.min,
                    strategyEvaluation.recommended_leverage.max
                  )}
                  )
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`text-xs ${getConfidenceColor(
                    strategyEvaluation.recommended_leverage.confidence
                  )}`}
                >
                  {Math.round(strategyEvaluation.recommended_leverage.confidence * 100)}%
                  confidence
                </span>
                <span className="text-xs text-muted-foreground">
                  •{' '}
                  {getLeverageRiskLabel(
                    strategyEvaluation.recommended_leverage.value,
                    strategyEvaluation.recommended_leverage.max
                  )}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Direction Signals Detail Row */}
        {strategyEvaluation.direction_signals && (
          <div className="mt-3 pt-3 border-t border-primary/10">
            <p className="text-xs text-muted-foreground mb-2">Direction Signals</p>
            <div className="flex flex-wrap gap-3">
              {Object.entries(strategyEvaluation.direction_signals).map(
                ([signal, value]) => (
                  <div key={signal} className="flex items-center gap-1.5">
                    <span className="text-xs text-muted-foreground">
                      {DIRECTION_SIGNAL_LABELS[
                        signal as keyof typeof DIRECTION_SIGNAL_LABELS
                      ] || signal}
                      :
                    </span>
                    <span className={`text-xs font-medium ${getSignalStatusColor(value)}`}>
                      {getSignalStatusLabel(value)}
                    </span>
                  </div>
                )
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Combined State:{' '}
              <span className="font-medium text-foreground">
                {COMBINED_STATE_LABELS[strategyEvaluation.combined_state] ||
                  strategyEvaluation.combined_state}
              </span>
            </p>
          </div>
        )}

        <p className="text-xs text-muted-foreground mt-3">
          Last updated: {new Date(strategyEvaluation.timestamp).toLocaleString()}
        </p>
      </div>

      {/* Per-Regime Entry/Exit Evaluation */}
      {Object.entries(strategyEvaluation.regimes).map(([regime, evaluation]) => {
        const availableDirections = getAvailableDirections(evaluation);
        const hasLongSignal = getEntryEvaluation(evaluation, 'long')?.entry_possible;
        const hasShortSignal = getEntryEvaluation(evaluation, 'short')?.entry_possible;

        return (
          <div
            key={regime}
            className={`p-4 rounded-lg border ${
              evaluation.is_active
                ? 'border-primary bg-primary/5'
                : 'border-border bg-muted/20'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold flex items-center gap-2">
                {regime.replace('_', ' ')}
                {evaluation.is_active && (
                  <Badge variant="default" className="ml-2">
                    ACTIVE
                  </Badge>
                )}
              </h4>
              <div className="flex items-center gap-2">
                {hasLongSignal && (
                  <Badge variant="default" className="bg-green-600">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Long ↑
                  </Badge>
                )}
                {hasShortSignal && (
                  <Badge variant="default" className="bg-red-600">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Short ↓
                  </Badge>
                )}
              </div>
            </div>

            {/* Direction Tabs for Long/Short */}
            <div className="space-y-4">
              {availableDirections.map((direction: TradeDirection) => {
                const entryEval = getEntryEvaluation(evaluation, direction);
                const exitEval = getExitEvaluation(evaluation, direction);

                if (!entryEval) return null;

                return (
                  <div
                    key={direction}
                    className={`p-3 rounded-lg border-l-4 ${DIRECTION_BG_COLORS[direction]} ${
                      direction === 'long'
                        ? 'border-l-green-500'
                        : 'border-l-red-500'
                    }`}
                  >
                    <h5
                      className={`text-sm font-semibold mb-3 ${DIRECTION_COLORS[direction]}`}
                    >
                      {DIRECTION_LABELS[direction]} Entry/Exit
                    </h5>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                      {/* Entry Conditions */}
                      <div className="space-y-4">
                        <EntryConditionsDisplay
                          entry={entryEval}
                          regime={regime as RegimeType}
                        />

                        {entryEval.aggregation === 'weighted_avg' && (
                          <EntryScoreBar
                            score={entryEval.score}
                            maxScore={entryEval.max_score}
                            threshold={entryEval.threshold}
                            entryPossible={entryEval.entry_possible}
                            aggregation={entryEval.aggregation}
                            conditions={entryEval.conditions}
                          />
                        )}
                      </div>

                      {/* Exit Rules */}
                      {exitEval && (
                        <ExitRulesDisplay
                          exit={exitEval}
                          currentPrice={strategyEvaluation.current_price}
                          regimeType={regime as 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY'}
                        />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
