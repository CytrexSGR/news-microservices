/**
 * ExitRulesDisplay Component
 *
 * Displays exit rules for a trading strategy with hypothetical price levels.
 * Shows:
 * - Current market price
 * - Individual exit rules with icons
 * - Hypothetical price targets if entering at current price
 * - Price differences and percentages (color-coded)
 */

import {
  TrendingUp,
  RefreshCw,
  StopCircle,
  Shuffle,
  Clock,
  Activity,
  HelpCircle,
  type LucideIcon
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import type { ExitEvaluation, ExitRuleEvaluation, ExitRuleType } from '@/types/strategy-evaluation';
import { formatPrice } from '@/features/trading/utils/formatters';

interface ExitRulesDisplayProps {
  exit: ExitEvaluation;
  currentPrice: number;
  regimeType?: 'TREND' | 'CONSOLIDATION' | 'HIGH_VOLATILITY';
  className?: string;
}

/**
 * Get icon for exit rule type
 */
function getExitRuleIcon(type: ExitRuleType): LucideIcon {
  const icons: Record<ExitRuleType, LucideIcon> = {
    'take_profit': TrendingUp,
    'trailing_stop': RefreshCw,
    'stop_loss': StopCircle,
    'regime_change': Shuffle,
    'time_based': Clock,
    'rsi_normalization': Activity,
    'bb_middle': Activity,
  };
  return icons[type] || HelpCircle;
}

/**
 * Format price difference with sign, absolute value, and percentage
 */
function formatPriceDiff(current: number, target: number): {
  absolute: string;
  percentage: string;
  isPositive: boolean;
  sign: string;
} {
  const diff = target - current;
  const pct = (diff / current) * 100;
  const isPositive = diff >= 0;
  const sign = isPositive ? '+' : '';

  return {
    absolute: `${sign}$${Math.abs(diff).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    percentage: `${sign}${pct.toFixed(2)}%`,
    isPositive,
    sign
  };
}

/**
 * Format rule description based on type and values
 */
function formatRuleDescription(rule: ExitRuleEvaluation): string {
  switch(rule.type) {
    case 'take_profit':
      return `Take Profit: ${(rule.value! * 100).toFixed(1)}%`;

    case 'trailing_stop':
      return `Trailing Stop: activated at ${(rule.activation! * 100).toFixed(1)}%, offset ${(rule.offset! * 100).toFixed(1)}%`;

    case 'stop_loss':
      return rule.description || 'Stop Loss';

    case 'regime_change':
      return rule.description || 'Regime Change → Exit Position';

    case 'time_based':
      return rule.description || `Time-Based Exit (${rule.max_bars} bars)`;

    case 'rsi_normalization':
      return rule.description || 'RSI Normalization Exit';

    case 'bb_middle':
      return rule.description || 'Bollinger Band Middle Exit';

    default:
      return rule.description;
  }
}

/**
 * Get hypothetical level display info for a rule
 */
function getHypotheticalLevel(
  rule: ExitRuleEvaluation,
  currentPrice: number,
  hypotheticalLevels: ExitEvaluation['hypothetical_levels']
): { price: number; label: string } | null {
  switch(rule.type) {
    case 'take_profit':
      return {
        price: hypotheticalLevels.take_profit,
        label: 'Target Price'
      };

    case 'stop_loss':
      return {
        price: hypotheticalLevels.stop_loss,
        label: 'Stop Loss Price'
      };

    case 'trailing_stop':
      if (hypotheticalLevels.trailing_activation) {
        return {
          price: hypotheticalLevels.trailing_activation,
          label: 'Activation Price'
        };
      }
      return null;

    default:
      return null;
  }
}

export function ExitRulesDisplay({
  exit,
  currentPrice,
  regimeType,
  className = ''
}: ExitRulesDisplayProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg">
          Exit Rules {regimeType && <span className="text-muted-foreground">({regimeType})</span>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Price */}
        <div className="pb-3 border-b">
          <p className="text-sm text-muted-foreground mb-1">Current Price</p>
          <p className="text-2xl font-bold font-mono">
            {formatPrice(currentPrice)}
          </p>
        </div>

        {/* Exit Rules */}
        <div className="space-y-3">
          {exit.rules.map((rule, index) => {
            const Icon = getExitRuleIcon(rule.type);
            const hypotheticalLevel = getHypotheticalLevel(rule, currentPrice, exit.hypothetical_levels);

            return (
              <div
                key={index}
                className="p-3 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors"
              >
                {/* Rule Header */}
                <div className="flex items-start gap-2 mb-2">
                  <Icon className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">
                      {formatRuleDescription(rule)}
                    </p>
                  </div>
                </div>

                {/* Hypothetical Level */}
                {hypotheticalLevel && (
                  <div className="ml-6 space-y-1">
                    <div className="flex items-baseline gap-2 flex-wrap">
                      <span className="text-xs text-muted-foreground">
                        → If entry now:
                      </span>
                      <span className="font-mono font-semibold">
                        {formatPrice(hypotheticalLevel.price)}
                      </span>
                    </div>

                    {(() => {
                      const diff = formatPriceDiff(currentPrice, hypotheticalLevel.price);
                      return (
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-xs font-medium ${
                            diff.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                          }`}>
                            {diff.absolute}
                          </span>
                          <span className={`text-xs font-medium ${
                            diff.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                          }`}>
                            ({diff.percentage})
                          </span>
                        </div>
                      );
                    })()}
                  </div>
                )}

                {/* Special handling for trailing stop */}
                {rule.type === 'trailing_stop' && hypotheticalLevel && rule.offset && (
                  <div className="ml-6 mt-1">
                    <span className="text-xs text-muted-foreground">
                      → Trail offset: {formatPrice(currentPrice * rule.offset)}
                    </span>
                  </div>
                )}

                {/* Special handling for stop loss with ATR */}
                {rule.type === 'stop_loss' && exit.hypothetical_levels.atr_value && (
                  <div className="ml-6 mt-1">
                    <span className="text-xs text-muted-foreground">
                      (ATR: {formatPrice(exit.hypothetical_levels.atr_value)})
                    </span>
                  </div>
                )}

                {/* Regime change - no price level */}
                {rule.type === 'regime_change' && !hypotheticalLevel && (
                  <div className="ml-6">
                    <span className="text-xs text-muted-foreground">
                      → Exit when market regime changes
                    </span>
                  </div>
                )}
              </div>
            );
          })}

          {/* No rules configured */}
          {exit.rules.length === 0 && (
            <div className="text-center py-6 text-muted-foreground">
              <p className="text-sm">No exit rules configured</p>
            </div>
          )}
        </div>

        {/* Summary Footer - if applicable */}
        {exit.rules.length > 0 && exit.hypothetical_levels && (
          <div className="pt-3 border-t space-y-2">
            <div className="grid grid-cols-2 gap-3 text-xs">
              {exit.hypothetical_levels.take_profit && (
                <div>
                  <p className="text-muted-foreground mb-0.5">Take Profit</p>
                  <p className="font-mono font-semibold text-green-600 dark:text-green-400">
                    {formatPrice(exit.hypothetical_levels.take_profit)}
                  </p>
                  <p className="text-muted-foreground">
                    +{(exit.hypothetical_levels.take_profit_pct * 100).toFixed(2)}%
                  </p>
                </div>
              )}

              {exit.hypothetical_levels.stop_loss && (
                <div>
                  <p className="text-muted-foreground mb-0.5">Stop Loss</p>
                  <p className="font-mono font-semibold text-red-600 dark:text-red-400">
                    {formatPrice(exit.hypothetical_levels.stop_loss)}
                  </p>
                  <p className="text-muted-foreground">
                    -{(exit.hypothetical_levels.stop_loss_pct * 100).toFixed(2)}%
                  </p>
                </div>
              )}
            </div>

            {exit.hypothetical_levels.atr_value && (
              <div className="pt-2 border-t">
                <p className="text-xs text-muted-foreground">
                  Current ATR: <span className="font-mono font-medium text-foreground">
                    {formatPrice(exit.hypothetical_levels.atr_value)}
                  </span>
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
