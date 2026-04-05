/**
 * RiskManagementTab Component
 *
 * Displays risk management settings per regime including stop loss,
 * position sizing, and leverage configuration.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Shield } from 'lucide-react';
import type { StrategyDefinition } from '../../types';
import { EditableField } from '../shared/EditableField';
import { useStrategyEditContext } from '../../context';
import type { StrategyEvaluationResponse } from '@/types/strategy-evaluation';
import {
  formatLeverage,
  formatLeverageRange,
  getLeverageColor,
  getLeverageBgColor,
  getLeveragePercentage,
  getLeverageRiskLabel,
} from '@/types/strategy-evaluation';

interface RiskManagementTabProps {
  definition: StrategyDefinition;
  strategyEvaluation?: StrategyEvaluationResponse | null;
}

// ============================================================================
// Sub-components for Editable Fields
// ============================================================================

interface LeverageRangeEditorProps {
  regime: string;
  minLeverage: number;
  maxLeverage: number;
}

/**
 * Editable leverage range component with graceful fallback
 */
function LeverageRangeEditor({ regime, minLeverage, maxLeverage }: LeverageRangeEditorProps) {
  try {
    const { isEditMode, updateRiskSetting, isPending } = useStrategyEditContext();

    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Range:</span>
        <div className="flex items-center gap-1">
          <EditableField
            value={minLeverage}
            type="number"
            canEdit={isEditMode && !isPending}
            showEditIndicator={isEditMode}
            onSave={(value) => updateRiskSetting(regime, 'leverage', 'min', value as number)}
            className="inline-flex"
            inputClassName="w-16"
            min={1}
            max={maxLeverage - 1}
            step={1}
            label="Min"
            suffix="x"
          />
          <span className="text-sm">-</span>
          <EditableField
            value={maxLeverage}
            type="number"
            canEdit={isEditMode && !isPending}
            showEditIndicator={isEditMode}
            onSave={(value) => updateRiskSetting(regime, 'leverage', 'max', value as number)}
            className="inline-flex"
            inputClassName="w-16"
            min={minLeverage + 1}
            max={125}
            step={1}
            label="Max"
            suffix="x"
          />
        </div>
      </div>
    );
  } catch {
    // Fallback: Render static Badge if not wrapped in StrategyEditProvider
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Range:</span>
        <Badge>
          {minLeverage}x - {maxLeverage}x
        </Badge>
      </div>
    );
  }
}

interface MaxRiskEditorProps {
  regime: string;
  maxRiskPerTrade: number;
}

/**
 * Editable max risk per trade component
 */
function MaxRiskEditor({ regime, maxRiskPerTrade }: MaxRiskEditorProps) {
  try {
    const { isEditMode, updateRiskSetting, isPending } = useStrategyEditContext();

    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Max Risk:</span>
        <EditableField
          value={(maxRiskPerTrade * 100).toFixed(2)}
          type="number"
          canEdit={isEditMode && !isPending}
          showEditIndicator={isEditMode}
          onSave={(value) => updateRiskSetting(regime, 'positionSize', 'maxRiskPerTrade', Number(value) / 100)}
          className="inline-flex"
          inputClassName="w-20"
          min={0.1}
          max={10}
          step={0.1}
          label="Max Risk"
          suffix="%"
        />
      </div>
    );
  } catch {
    // Fallback: Render static Badge if not wrapped in StrategyEditProvider
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Max Risk:</span>
        <Badge>
          {(maxRiskPerTrade * 100).toFixed(2)}%
        </Badge>
      </div>
    );
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function RiskManagementTab({
  definition,
  strategyEvaluation,
}: RiskManagementTabProps) {
  return (
    <div className="space-y-4">
      {Object.entries(definition.logic).map(([regime, config]) => (
        <Card key={regime}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              {regime} - Risk Management
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Stop Loss */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <h4 className="font-semibold mb-2">Stop Loss</h4>
              <div className="space-y-2">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Formula:</p>
                  <code className="text-sm font-mono block p-2 bg-background rounded">
                    {config.risk?.stopLoss?.formula || 'N/A'}
                  </code>
                </div>
                <p className="text-xs text-muted-foreground">
                  {config.risk?.stopLoss?.description}
                </p>
                {config.risk?.stopLoss?.trailingStop && (
                  <Badge variant="secondary">Trailing Stop Enabled</Badge>
                )}
              </div>
            </div>

            {/* Position Size */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <h4 className="font-semibold mb-2">Position Sizing</h4>
              <div className="space-y-2">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Formula:</p>
                  <code className="text-sm font-mono block p-2 bg-background rounded">
                    {config.risk?.positionSize?.formula || 'N/A'}
                  </code>
                </div>
                <p className="text-xs text-muted-foreground">
                  {config.risk?.positionSize?.description}
                </p>
                {config.risk?.positionSize?.maxRiskPerTrade && (
                  <MaxRiskEditor
                    regime={regime}
                    maxRiskPerTrade={config.risk.positionSize.maxRiskPerTrade}
                  />
                )}
              </div>
            </div>

            {/* Leverage */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <h4 className="font-semibold mb-2">Leverage</h4>
              <div className="space-y-2">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Formula:</p>
                  <code className="text-sm font-mono block p-2 bg-background rounded">
                    {config.risk?.leverage?.formula || 'N/A'}
                  </code>
                </div>
                <p className="text-xs text-muted-foreground">
                  {config.risk?.leverage?.description}
                </p>
                {config.risk?.leverage?.min !== undefined &&
                  config.risk?.leverage?.max !== undefined && (
                    <LeverageRangeEditor
                      regime={regime}
                      minLeverage={config.risk.leverage.min}
                      maxLeverage={config.risk.leverage.max}
                    />
                  )}

                {/* Live Leverage Calculation - shown when this regime is active */}
                {strategyEvaluation?.current_regime === regime &&
                  strategyEvaluation?.recommended_leverage && (
                    <div className="mt-4 p-3 bg-primary/5 border border-primary/20 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-sm font-semibold text-primary">
                          Live Recommendation
                        </span>
                        <Badge variant="outline" className="text-xs">
                          Current Market
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-2xl font-bold ${getLeverageColor(
                              strategyEvaluation.recommended_leverage.value,
                              strategyEvaluation.recommended_leverage.max
                            )}`}
                          >
                            {formatLeverage(strategyEvaluation.recommended_leverage.value)}
                          </span>
                          <div className="text-xs text-muted-foreground">
                            <p>
                              {getLeverageRiskLabel(
                                strategyEvaluation.recommended_leverage.value,
                                strategyEvaluation.recommended_leverage.max
                              )}
                            </p>
                            <p>
                              {Math.round(
                                strategyEvaluation.recommended_leverage.confidence * 100
                              )}
                              % confidence
                            </p>
                          </div>
                        </div>
                        <div className="flex-1 max-w-xs">
                          <div className="h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getLeverageBgColor(
                                strategyEvaluation.recommended_leverage.value,
                                strategyEvaluation.recommended_leverage.max
                              )}`}
                              style={{
                                width: `${getLeveragePercentage(
                                  strategyEvaluation.recommended_leverage.value,
                                  strategyEvaluation.recommended_leverage.min,
                                  strategyEvaluation.recommended_leverage.max
                                )}%`,
                              }}
                            />
                          </div>
                          <div className="flex justify-between text-xs text-muted-foreground mt-1">
                            <span>{strategyEvaluation.recommended_leverage.min}x</span>
                            <span>{strategyEvaluation.recommended_leverage.max}x</span>
                          </div>
                        </div>
                      </div>
                      {/* Input Values */}
                      <div className="mt-2 pt-2 border-t border-primary/10">
                        <p className="text-xs text-muted-foreground mb-1">
                          Indicator Values:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(
                            strategyEvaluation.recommended_leverage.inputs
                          ).map(([key, value]) => (
                            <code
                              key={key}
                              className="text-xs bg-background px-2 py-0.5 rounded"
                            >
                              {key} ={' '}
                              {typeof value === 'number' ? value.toFixed(2) : String(value)}
                            </code>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
