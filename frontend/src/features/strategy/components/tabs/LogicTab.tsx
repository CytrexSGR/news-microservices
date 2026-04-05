/**
 * LogicTab Component
 *
 * Displays entry/exit logic configuration per regime including
 * long and short conditions, aggregation, and thresholds.
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Target, CheckCircle2 } from 'lucide-react';
import type { StrategyDefinition } from '../../types';
import { EditableField } from '../shared/EditableField';
import { useStrategyEditContext } from '../../context';

interface LogicTabProps {
  definition: StrategyDefinition;
}

interface EntryConfig {
  conditions?: Array<{
    expression: string;
    confidence: number;
    description: string;
  }>;
  aggregation?: string;
  threshold?: number;
  description?: string;
}

interface ExitConfig {
  rules?: Array<{
    type: string;
    value?: number;
    description: string;
  }>;
}

// ============================================================================
// Sub-components for Editable Fields
// ============================================================================

interface ConditionConfidenceEditorProps {
  regime: string;
  direction: 'long' | 'short';
  conditionIndex: number;
  confidence: number;
}

/**
 * Editable condition confidence component
 */
function ConditionConfidenceEditor({
  regime,
  direction,
  conditionIndex,
  confidence,
}: ConditionConfidenceEditorProps) {
  try {
    const { isEditMode, updateRegimeLogic, isPending } = useStrategyEditContext();
    const entryKey = direction === 'long' ? 'entry_long' : 'entry_short';

    return (
      <EditableField
        value={(confidence * 100).toFixed(0)}
        type="number"
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={(value) =>
          updateRegimeLogic(
            regime,
            `${entryKey}.conditions[${conditionIndex}].confidence`,
            Number(value) / 100
          )
        }
        className="shrink-0"
        inputClassName="w-16"
        min={0}
        max={100}
        step={5}
        suffix="%"
        label="Confidence"
      />
    );
  } catch {
    return (
      <Badge variant="outline" className="shrink-0">
        {(confidence * 100).toFixed(0)}%
      </Badge>
    );
  }
}

interface ThresholdEditorProps {
  regime: string;
  direction: 'long' | 'short';
  threshold: number;
}

/**
 * Editable threshold component
 */
function ThresholdEditor({ regime, direction, threshold }: ThresholdEditorProps) {
  try {
    const { isEditMode, updateRegimeLogic, isPending } = useStrategyEditContext();
    const entryKey = direction === 'long' ? 'entry_long' : 'entry_short';

    return (
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">Threshold:</span>
        <EditableField
          value={(threshold * 100).toFixed(0)}
          type="number"
          canEdit={isEditMode && !isPending}
          showEditIndicator={isEditMode}
          onSave={(value) => updateRegimeLogic(regime, `${entryKey}.threshold`, Number(value) / 100)}
          className="inline-flex"
          inputClassName="w-16"
          min={0}
          max={100}
          step={5}
          suffix="%"
        />
      </div>
    );
  } catch {
    return (
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">Threshold:</span>
        <Badge variant="secondary">{((threshold || 0) * 100).toFixed(0)}%</Badge>
      </div>
    );
  }
}

interface AggregationEditorProps {
  regime: string;
  direction: 'long' | 'short';
  aggregation: string;
}

/**
 * Editable aggregation type component
 */
function AggregationEditor({ regime, direction, aggregation }: AggregationEditorProps) {
  try {
    const { isEditMode, updateRegimeLogic, isPending } = useStrategyEditContext();
    const entryKey = direction === 'long' ? 'entry_long' : 'entry_short';

    const options = [
      { value: 'AND', label: 'AND' },
      { value: 'OR', label: 'OR' },
      { value: 'WEIGHTED_AVG', label: 'Weighted Avg' },
    ];

    return (
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">Aggregation:</span>
        <EditableField
          value={aggregation}
          type="select"
          canEdit={isEditMode && !isPending}
          showEditIndicator={isEditMode}
          onSave={(value) => updateRegimeLogic(regime, `${entryKey}.aggregation`, value as string)}
          className="inline-flex"
          options={options}
        />
      </div>
    );
  } catch {
    return (
      <div className="flex items-center gap-2">
        <span className="text-muted-foreground">Aggregation:</span>
        <Badge variant="secondary">{aggregation}</Badge>
      </div>
    );
  }
}

interface ExitRuleValueEditorProps {
  regime: string;
  direction: 'long' | 'short';
  ruleIndex: number;
  value: number;
}

/**
 * Editable exit rule value component
 */
function ExitRuleValueEditor({ regime, direction, ruleIndex, value }: ExitRuleValueEditorProps) {
  try {
    const { isEditMode, updateRegimeLogic, isPending } = useStrategyEditContext();
    const exitKey = direction === 'long' ? 'exit_long' : 'exit_short';

    return (
      <EditableField
        value={(value * 100).toFixed(1)}
        type="number"
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={(v) => updateRegimeLogic(regime, `${exitKey}.rules[${ruleIndex}].value`, Number(v) / 100)}
        className="inline-flex"
        inputClassName="w-16"
        min={-50}
        max={100}
        step={0.5}
        suffix="%"
      />
    );
  } catch {
    return <span className="font-mono text-xs">{(value * 100).toFixed(1)}%</span>;
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function LogicTab({ definition }: LogicTabProps) {
  return (
    <div className="space-y-4">
      {Object.entries(definition.logic).map(([regime, config]) => {
        // Support both new (entry_long/entry_short) and legacy (entry) formats
        const entryLong: EntryConfig | undefined =
          (config as any).entry_long || (config as any).entry;
        const entryShort: EntryConfig | undefined = (config as any).entry_short;
        const exitLong: ExitConfig | undefined =
          (config as any).exit_long || (config as any).exit;
        const exitShort: ExitConfig | undefined = (config as any).exit_short;
        const hasLong = !!entryLong;
        const hasShort = !!entryShort;

        return (
          <Card key={regime}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    {regime}
                  </CardTitle>
                  <CardDescription>
                    {entryLong?.description ||
                      entryShort?.description ||
                      'Regime logic configuration'}
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  {hasLong && (
                    <Badge variant="default" className="gap-1 bg-green-600">
                      <CheckCircle2 className="h-3 w-3" />
                      Long
                    </Badge>
                  )}
                  {hasShort && (
                    <Badge variant="default" className="gap-1 bg-red-600">
                      <CheckCircle2 className="h-3 w-3" />
                      Short
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Long Entry/Exit Section */}
              {entryLong && (
                <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950/20 border-l-4 border-green-500">
                  <h4 className="font-semibold mb-3 flex items-center gap-2 text-green-700 dark:text-green-400">
                    <Target className="h-4 w-4" />
                    Long Entry ({entryLong.conditions?.length || 0} conditions)
                  </h4>
                  <div className="space-y-2">
                    {(entryLong.conditions || []).map((condition, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-white/50 dark:bg-black/20 rounded-lg"
                      >
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <code className="text-sm font-mono">
                            {condition.expression}
                          </code>
                          <ConditionConfidenceEditor
                            regime={regime}
                            direction="long"
                            conditionIndex={idx}
                            confidence={condition.confidence}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {condition.description}
                        </p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex items-center gap-4 text-sm">
                    <AggregationEditor
                      regime={regime}
                      direction="long"
                      aggregation={entryLong.aggregation || 'AND'}
                    />
                    <ThresholdEditor
                      regime={regime}
                      direction="long"
                      threshold={entryLong.threshold || 0}
                    />
                  </div>

                  {/* Long Exit Rules */}
                  {exitLong && exitLong.rules && exitLong.rules.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-green-200 dark:border-green-800">
                      <h5 className="font-semibold mb-2 text-sm">
                        Long Exit Rules ({exitLong.rules.length})
                      </h5>
                      <div className="space-y-2">
                        {exitLong.rules.map((rule, idx) => (
                          <div
                            key={idx}
                            className="p-2 bg-white/50 dark:bg-black/20 rounded-lg"
                          >
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{rule.type}</Badge>
                              {rule.value !== undefined && (
                                <ExitRuleValueEditor
                                  regime={regime}
                                  direction="long"
                                  ruleIndex={idx}
                                  value={rule.value}
                                />
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              {rule.description}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Short Entry/Exit Section */}
              {entryShort && (
                <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950/20 border-l-4 border-red-500">
                  <h4 className="font-semibold mb-3 flex items-center gap-2 text-red-700 dark:text-red-400">
                    <Target className="h-4 w-4" />
                    Short Entry ({entryShort.conditions?.length || 0} conditions)
                  </h4>
                  <div className="space-y-2">
                    {(entryShort.conditions || []).map((condition, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-white/50 dark:bg-black/20 rounded-lg"
                      >
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <code className="text-sm font-mono">
                            {condition.expression}
                          </code>
                          <ConditionConfidenceEditor
                            regime={regime}
                            direction="short"
                            conditionIndex={idx}
                            confidence={condition.confidence}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {condition.description}
                        </p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex items-center gap-4 text-sm">
                    <AggregationEditor
                      regime={regime}
                      direction="short"
                      aggregation={entryShort.aggregation || 'AND'}
                    />
                    <ThresholdEditor
                      regime={regime}
                      direction="short"
                      threshold={entryShort.threshold || 0}
                    />
                  </div>

                  {/* Short Exit Rules */}
                  {exitShort && exitShort.rules && exitShort.rules.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-red-200 dark:border-red-800">
                      <h5 className="font-semibold mb-2 text-sm">
                        Short Exit Rules ({exitShort.rules.length})
                      </h5>
                      <div className="space-y-2">
                        {exitShort.rules.map((rule, idx) => (
                          <div
                            key={idx}
                            className="p-2 bg-white/50 dark:bg-black/20 rounded-lg"
                          >
                            <div className="flex items-center gap-2">
                              <Badge variant="outline">{rule.type}</Badge>
                              {rule.value !== undefined && (
                                <ExitRuleValueEditor
                                  regime={regime}
                                  direction="short"
                                  ruleIndex={idx}
                                  value={rule.value}
                                />
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">
                              {rule.description}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
