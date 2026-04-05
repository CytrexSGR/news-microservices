/**
 * RegimeDetectionEditor Component
 *
 * Configures how market regimes are detected
 * Three providers: rule_based, ml_based, hybrid
 * Each provider has different config schema
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Label } from '@/components/ui/Label'
import type { Strategy } from '@/types/strategy'

interface RegimeDetectionEditorProps {
  strategy: Strategy
  onChange?: (field: string, value: any) => void
}

type RegimeProvider = 'rule_based' | 'ml_based' | 'hybrid'

export function RegimeDetectionEditor({ strategy, onChange }: RegimeDetectionEditorProps) {
  const regimeDetection = strategy.definition?.regimeDetection || {
    provider: 'rule_based',
    config: {},
  }

  const provider = (regimeDetection.provider as RegimeProvider) || 'rule_based'

  const handleProviderChange = (newProvider: RegimeProvider) => {
    onChange?.('regimeDetection.provider', newProvider)
    // Reset config when provider changes
    onChange?.('regimeDetection.config', getDefaultConfig(newProvider))
  }

  const handleConfigChange = (key: string, value: any) => {
    onChange?.(`regimeDetection.config.${key}`, value)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Regime Detection Configuration</CardTitle>
        <CardDescription>
          Configure how market regimes (TREND, CONSOLIDATION, HIGH_VOLATILITY) are identified
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Provider Selection */}
        <div className="space-y-2">
          <Label htmlFor="provider">
            Detection Method
            <span className="text-destructive ml-1">*</span>
          </Label>
          <select
            id="provider"
            value={provider}
            onChange={(e) => handleProviderChange(e.target.value as RegimeProvider)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <option value="rule_based">Rule-Based (Manual Thresholds)</option>
            <option value="ml_based">ML-Based (Machine Learning Model)</option>
            <option value="hybrid">Hybrid (Rule + ML Combination)</option>
          </select>
          <p className="text-xs text-muted-foreground">
            {provider === 'rule_based' && 'Uses ADX, BBW, and ATR thresholds to detect regimes'}
            {provider === 'ml_based' && 'Uses a trained ML model for regime classification'}
            {provider === 'hybrid' && 'Combines rule-based and ML predictions'}
          </p>
        </div>

        {/* Provider-Specific Configuration */}
        <div className="border-t pt-6">
          {provider === 'rule_based' && (
            <RuleBasedConfig
              config={regimeDetection.config}
              onChange={handleConfigChange}
            />
          )}

          {provider === 'ml_based' && (
            <MLBasedConfig
              config={regimeDetection.config}
              onChange={handleConfigChange}
            />
          )}

          {provider === 'hybrid' && (
            <HybridConfig
              config={regimeDetection.config}
              onChange={handleConfigChange}
            />
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Rule-Based Configuration
 * Uses indicator thresholds (ADX, BBW, ATR)
 */
interface ConfigProps {
  config: any
  onChange: (key: string, value: any) => void
}

function RuleBasedConfig({ config, onChange }: ConfigProps) {
  const adxThreshold = config.adx_threshold ?? 25
  const bbwThreshold = config.bbw_threshold ?? 0.02
  const atrThreshold = config.atr_threshold ?? 0.5

  return (
    <div className="space-y-6">
      <h4 className="font-semibold text-sm">Rule-Based Thresholds</h4>

      {/* ADX Threshold */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="adx-threshold">ADX Threshold (Trend Strength)</Label>
          <span className="text-sm font-medium">{adxThreshold}</span>
        </div>
        <input
          id="adx-threshold"
          type="range"
          min="0"
          max="100"
          step="1"
          value={adxThreshold}
          onChange={(e) => onChange('adx_threshold', Number(e.target.value))}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          ADX &gt; {adxThreshold} = TREND regime (strong directional movement)
        </p>
      </div>

      {/* BBW Threshold */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="bbw-threshold">BBW Threshold (Volatility)</Label>
          <span className="text-sm font-medium">{bbwThreshold.toFixed(3)}</span>
        </div>
        <input
          id="bbw-threshold"
          type="range"
          min="0"
          max="0.1"
          step="0.001"
          value={bbwThreshold}
          onChange={(e) => onChange('bbw_threshold', Number(e.target.value))}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          BBW &gt; {bbwThreshold.toFixed(3)} = HIGH_VOLATILITY regime (wide Bollinger Bands)
        </p>
      </div>

      {/* ATR Threshold */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="atr-threshold">ATR Threshold (Average True Range)</Label>
          <span className="text-sm font-medium">{atrThreshold.toFixed(2)}</span>
        </div>
        <input
          id="atr-threshold"
          type="range"
          min="0"
          max="10"
          step="0.1"
          value={atrThreshold}
          onChange={(e) => onChange('atr_threshold', Number(e.target.value))}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          ATR &gt; {atrThreshold.toFixed(2)} = Higher volatility signal
        </p>
      </div>

      <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
        <p className="font-medium">Logic:</p>
        <p>1. If ADX &gt; {adxThreshold} → TREND</p>
        <p>2. Else if BBW &gt; {bbwThreshold.toFixed(3)} → HIGH_VOLATILITY</p>
        <p>3. Else → CONSOLIDATION</p>
      </div>
    </div>
  )
}

/**
 * ML-Based Configuration
 * Uses trained model for classification
 */
function MLBasedConfig({ config, onChange }: ConfigProps) {
  const modelPath = config.model_path || ''
  const confidenceThreshold = config.confidence_threshold ?? 0.7
  const featureColumns = config.feature_columns || ['1h_ADX_14', '1h_BBW_20', '1h_ATR_14']

  return (
    <div className="space-y-6">
      <h4 className="font-semibold text-sm">ML Model Configuration</h4>

      {/* Model Path */}
      <div className="space-y-2">
        <Label htmlFor="model-path">Model Path</Label>
        <input
          id="model-path"
          type="text"
          value={modelPath}
          onChange={(e) => onChange('model_path', e.target.value)}
          placeholder="/models/regime_classifier.pkl"
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Path to trained scikit-learn or FreqAI model file
        </p>
      </div>

      {/* Feature Columns */}
      <div className="space-y-2">
        <Label htmlFor="features">Feature Columns (comma-separated)</Label>
        <input
          id="features"
          type="text"
          value={featureColumns.join(', ')}
          onChange={(e) => onChange('feature_columns', e.target.value.split(',').map(s => s.trim()))}
          placeholder="1h_ADX_14, 1h_BBW_20, 1h_ATR_14"
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Indicator columns used as model features
        </p>
      </div>

      {/* Confidence Threshold */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="confidence">Confidence Threshold</Label>
          <span className="text-sm font-medium">{(confidenceThreshold * 100).toFixed(0)}%</span>
        </div>
        <input
          id="confidence"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={confidenceThreshold}
          onChange={(e) => onChange('confidence_threshold', Number(e.target.value))}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          Minimum prediction confidence to accept regime classification
        </p>
      </div>
    </div>
  )
}

/**
 * Hybrid Configuration
 * Combines rule-based and ML predictions
 */
function HybridConfig({ config, onChange }: ConfigProps) {
  const ruleWeight = config.rule_weight ?? 0.4
  const mlWeight = config.ml_weight ?? 0.6
  const combineMethod = config.combine_method || 'weighted_avg'

  return (
    <div className="space-y-6">
      <h4 className="font-semibold text-sm">Hybrid Configuration</h4>

      {/* Combine Method */}
      <div className="space-y-2">
        <Label htmlFor="combine-method">Combination Method</Label>
        <select
          id="combine-method"
          value={combineMethod}
          onChange={(e) => onChange('combine_method', e.target.value)}
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="weighted_avg">Weighted Average</option>
          <option value="voting">Majority Voting</option>
          <option value="sequential">Sequential (Rule → ML if uncertain)</option>
        </select>
      </div>

      {/* Rule Weight */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="rule-weight">Rule-Based Weight</Label>
          <span className="text-sm font-medium">{(ruleWeight * 100).toFixed(0)}%</span>
        </div>
        <input
          id="rule-weight"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={ruleWeight}
          onChange={(e) => {
            const newRuleWeight = Number(e.target.value)
            onChange('rule_weight', newRuleWeight)
            onChange('ml_weight', 1 - newRuleWeight)
          }}
          className="w-full"
        />
      </div>

      {/* ML Weight (calculated) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="ml-weight">ML-Based Weight</Label>
          <span className="text-sm font-medium">{(mlWeight * 100).toFixed(0)}%</span>
        </div>
        <input
          id="ml-weight"
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={mlWeight}
          onChange={(e) => {
            const newMlWeight = Number(e.target.value)
            onChange('ml_weight', newMlWeight)
            onChange('rule_weight', 1 - newMlWeight)
          }}
          className="w-full"
        />
      </div>

      <div className="p-3 bg-muted rounded-lg text-xs space-y-1">
        <p className="font-medium">Combination:</p>
        <p>Rule-based: {(ruleWeight * 100).toFixed(0)}% • ML-based: {(mlWeight * 100).toFixed(0)}%</p>
        <p>Method: {combineMethod.replace('_', ' ')}</p>
      </div>
    </div>
  )
}

/**
 * Get default config based on provider
 */
function getDefaultConfig(provider: RegimeProvider): any {
  switch (provider) {
    case 'rule_based':
      return {
        adx_threshold: 25,
        bbw_threshold: 0.02,
        atr_threshold: 0.5,
      }
    case 'ml_based':
      return {
        model_path: '',
        feature_columns: ['1h_ADX_14', '1h_BBW_20', '1h_ATR_14'],
        confidence_threshold: 0.7,
      }
    case 'hybrid':
      return {
        rule_weight: 0.4,
        ml_weight: 0.6,
        combine_method: 'weighted_avg',
      }
    default:
      return {}
  }
}
