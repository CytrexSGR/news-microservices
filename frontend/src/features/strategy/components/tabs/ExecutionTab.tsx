/**
 * ExecutionTab Component
 *
 * Displays execution settings for a strategy including timeframe,
 * order types, protections, and regime transition behavior.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Settings } from 'lucide-react';
import type { StrategyDefinition } from '../../types';
import { EditableField } from '../shared/EditableField';
import { useStrategyEditContext } from '../../context';

interface ExecutionTabProps {
  definition: StrategyDefinition;
}

// ============================================================================
// Sub-components for Editable Fields
// ============================================================================

interface TimeframeEditorProps {
  timeframe: string;
}

/**
 * Editable timeframe selector
 */
function TimeframeEditor({ timeframe }: TimeframeEditorProps) {
  try {
    const { isEditMode, updateExecution, isPending } = useStrategyEditContext();

    const options = [
      { value: '1m', label: '1 Minute' },
      { value: '5m', label: '5 Minutes' },
      { value: '15m', label: '15 Minutes' },
      { value: '30m', label: '30 Minutes' },
      { value: '1h', label: '1 Hour' },
      { value: '4h', label: '4 Hours' },
      { value: '1d', label: '1 Day' },
    ];

    return (
      <EditableField
        value={timeframe}
        type="select"
        options={options}
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={(value) => updateExecution('timeframe', value as string)}
        label="Timeframe"
      />
    );
  } catch {
    return <Badge variant="outline">{timeframe}</Badge>;
  }
}

interface BooleanToggleEditorProps {
  field: 'canLong' | 'canShort';
  value: boolean;
  label: string;
}

/**
 * Editable boolean toggle
 */
function BooleanToggleEditor({ field, value, label }: BooleanToggleEditorProps) {
  try {
    const { isEditMode, updateExecution, isPending } = useStrategyEditContext();

    const options = [
      { value: 'true', label: 'Enabled' },
      { value: 'false', label: 'Disabled' },
    ];

    return (
      <EditableField
        value={value ? 'true' : 'false'}
        type="select"
        options={options}
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={(v) => updateExecution(field, v === 'true')}
        label={label}
        formatDisplay={(v) => (v === 'true' ? 'Enabled' : 'Disabled')}
      />
    );
  } catch {
    return value ? (
      <Badge variant="default">Enabled</Badge>
    ) : (
      <Badge variant="secondary">Disabled</Badge>
    );
  }
}

interface FillTimeoutEditorProps {
  fillTimeout: number;
}

/**
 * Editable fill timeout
 */
function FillTimeoutEditor({ fillTimeout }: FillTimeoutEditorProps) {
  try {
    const { isEditMode, updateExecution, isPending } = useStrategyEditContext();

    return (
      <EditableField
        value={fillTimeout}
        type="number"
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={(value) => updateExecution('fillTimeout', value as number)}
        inputClassName="w-20"
        min={1}
        max={3600}
        step={1}
        suffix="s"
        label="Fill Timeout"
      />
    );
  } catch {
    return <Badge variant="outline">{fillTimeout}s</Badge>;
  }
}

interface OrderTypeEditorProps {
  orderType: string;
  value: string;
}

/**
 * Editable order type
 */
function OrderTypeEditor({ orderType, value }: OrderTypeEditorProps) {
  try {
    const { isEditMode, updateDefinition, isPending } = useStrategyEditContext();

    const options = [
      { value: 'market', label: 'Market' },
      { value: 'limit', label: 'Limit' },
    ];

    return (
      <EditableField
        value={value}
        type="select"
        options={options}
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={async (newValue) => {
          // Need to update orderTypes object
          await updateDefinition({
            execution: {
              orderTypes: {
                [orderType]: newValue as string,
              },
            },
          } as any);
        }}
        label={orderType}
      />
    );
  } catch {
    return <Badge variant="secondary">{String(value)}</Badge>;
  }
}

interface RegimeTransitionEditorProps {
  regimeTransitionBehavior: {
    onRegimeChange: string;
    updateStops: boolean;
    updateTargets: boolean;
    description?: string;
  };
}

/**
 * Editable regime transition behavior
 */
function RegimeTransitionEditor({ regimeTransitionBehavior }: RegimeTransitionEditorProps) {
  try {
    const { isEditMode, updateDefinition, isPending } = useStrategyEditContext();

    const onRegimeChangeOptions = [
      { value: 'close_positions', label: 'Close Positions' },
      { value: 'keep_positions', label: 'Keep Positions' },
      { value: 'scale_down', label: 'Scale Down' },
    ];

    const boolOptions = [
      { value: 'true', label: 'Yes' },
      { value: 'false', label: 'No' },
    ];

    const updateRegimeTransition = async (key: string, value: string | boolean) => {
      await updateDefinition({
        execution: {
          regimeTransitionBehavior: {
            ...regimeTransitionBehavior,
            [key]: value,
          },
        },
      } as any);
    };

    return (
      <div className="p-3 bg-muted/50 rounded-lg space-y-2">
        <div className="flex justify-between items-center text-sm">
          <span className="text-muted-foreground">On Regime Change:</span>
          <EditableField
            value={regimeTransitionBehavior.onRegimeChange}
            type="select"
            options={onRegimeChangeOptions}
            canEdit={isEditMode && !isPending}
            showEditIndicator={isEditMode}
            onSave={(v) => updateRegimeTransition('onRegimeChange', v as string)}
            label="Action"
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-muted-foreground">Update Stops:</span>
          <EditableField
            value={regimeTransitionBehavior.updateStops ? 'true' : 'false'}
            type="select"
            options={boolOptions}
            canEdit={isEditMode && !isPending}
            showEditIndicator={isEditMode}
            onSave={(v) => updateRegimeTransition('updateStops', v === 'true')}
            formatDisplay={(v) => (v === 'true' ? 'Yes' : 'No')}
            label="Update Stops"
          />
        </div>
        <div className="flex justify-between items-center text-sm">
          <span className="text-muted-foreground">Update Targets:</span>
          <EditableField
            value={regimeTransitionBehavior.updateTargets ? 'true' : 'false'}
            type="select"
            options={boolOptions}
            canEdit={isEditMode && !isPending}
            showEditIndicator={isEditMode}
            onSave={(v) => updateRegimeTransition('updateTargets', v === 'true')}
            formatDisplay={(v) => (v === 'true' ? 'Yes' : 'No')}
            label="Update Targets"
          />
        </div>
        {regimeTransitionBehavior.description && (
          <p className="text-xs text-muted-foreground pt-2">
            {regimeTransitionBehavior.description}
          </p>
        )}
      </div>
    );
  } catch {
    // Fallback to static display
    return (
      <div className="p-3 bg-muted/50 rounded-lg space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">On Regime Change:</span>
          <Badge variant="secondary">{regimeTransitionBehavior.onRegimeChange}</Badge>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Update Stops:</span>
          <Badge variant={regimeTransitionBehavior.updateStops ? 'default' : 'secondary'}>
            {regimeTransitionBehavior.updateStops ? 'Yes' : 'No'}
          </Badge>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Update Targets:</span>
          <Badge variant={regimeTransitionBehavior.updateTargets ? 'default' : 'secondary'}>
            {regimeTransitionBehavior.updateTargets ? 'Yes' : 'No'}
          </Badge>
        </div>
        {regimeTransitionBehavior.description && (
          <p className="text-xs text-muted-foreground pt-2">
            {regimeTransitionBehavior.description}
          </p>
        )}
      </div>
    );
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function ExecutionTab({ definition }: ExecutionTabProps) {
  const { execution } = definition;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Execution Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Basic Settings */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Timeframe</p>
              <TimeframeEditor timeframe={execution.timeframe} />
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Long</p>
              <BooleanToggleEditor field="canLong" value={execution.canLong} label="Long" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Short</p>
              <BooleanToggleEditor field="canShort" value={execution.canShort} label="Short" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Fill Timeout</p>
              <FillTimeoutEditor fillTimeout={execution.fillTimeout} />
            </div>
          </div>

          {/* Order Types */}
          {execution.orderTypes && (
            <div>
              <h4 className="font-semibold mb-2">Order Types</h4>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(execution.orderTypes).map(([type, value]) => (
                  <div key={type} className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground capitalize">{type}:</span>
                    <OrderTypeEditor orderType={type} value={String(value)} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Protections */}
          {execution.protections && execution.protections.length > 0 && (
            <div>
              <h4 className="font-semibold mb-3">
                Protections ({execution.protections.length})
              </h4>
              <div className="space-y-2">
                {execution.protections.map((protection, idx) => (
                  <div key={idx} className="p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge>{protection.method}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">
                      {protection.description}
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(protection)
                        .filter(([key]) => !['method', 'description'].includes(key))
                        .map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="text-muted-foreground">{key}:</span>
                            <span className="font-mono">{String(value)}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Regime Transition Behavior */}
          {execution.regimeTransitionBehavior && (
            <div>
              <h4 className="font-semibold mb-2">Regime Transition Behavior</h4>
              <RegimeTransitionEditor
                regimeTransitionBehavior={execution.regimeTransitionBehavior}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
