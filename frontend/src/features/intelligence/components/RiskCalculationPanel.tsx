import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/Switch';
import { AlertCircle, Calculator, Loader2, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useRiskCalculation } from '../api/useRiskScore';
import type { RiskCalculateRequest } from '../api/intelligenceApi';

/**
 * Panel for calculating custom risk scores
 *
 * Features:
 * - Calculate risk for specific cluster (by ID)
 * - Calculate risk for entity names
 * - Calculate risk for raw text content
 * - Optional factor breakdown
 * - Shows contributing factors and risk delta
 */
export function RiskCalculationPanel() {
  const [mode, setMode] = useState<'cluster' | 'entities' | 'text'>('cluster');
  const [clusterId, setClusterId] = useState('');
  const [entities, setEntities] = useState('');
  const [text, setText] = useState('');
  const [includeFactors, setIncludeFactors] = useState(true);

  const { mutate, data, isPending, error, reset } = useRiskCalculation();

  const handleCalculate = () => {
    const request: RiskCalculateRequest = {
      include_factors: includeFactors,
    };

    if (mode === 'cluster' && clusterId.trim()) {
      request.cluster_id = clusterId.trim();
    } else if (mode === 'entities' && entities.trim()) {
      request.entities = entities.split(',').map((name) => name.trim()).filter(Boolean);
    } else if (mode === 'text' && text.trim()) {
      request.text = text.trim();
    } else {
      return; // Nothing to calculate
    }

    mutate(request);
  };

  const handleClear = () => {
    setClusterId('');
    setEntities('');
    setText('');
    setIncludeFactors(true);
    reset();
  };

  const canCalculate = () => {
    if (mode === 'cluster') return clusterId.trim().length > 0;
    if (mode === 'entities') return entities.trim().length > 0;
    if (mode === 'text') return text.trim().length >= 10;
    return false;
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-500';
      case 'high':
        return 'bg-orange-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
      default:
        return 'bg-green-500';
    }
  };

  const getRiskTextColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'text-red-500';
      case 'high':
        return 'text-orange-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
      default:
        return 'text-green-500';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5" />
          Risk Calculation
        </CardTitle>
        <CardDescription>
          Calculate custom risk scores for clusters or entity groups
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Mode Selection */}
        <div className="flex gap-2">
          <Button
            variant={mode === 'cluster' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode('cluster')}
          >
            By Cluster
          </Button>
          <Button
            variant={mode === 'entities' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode('entities')}
          >
            By Entities
          </Button>
          <Button
            variant={mode === 'text' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setMode('text')}
          >
            By Text
          </Button>
        </div>

        {/* Input Section */}
        <div className="space-y-4">
          {mode === 'cluster' && (
            <div>
              <Label htmlFor="clusterId">Cluster ID</Label>
              <Input
                id="clusterId"
                placeholder="e.g., abc-123-def-456"
                value={clusterId}
                onChange={(e) => setClusterId(e.target.value)}
                className="mt-1"
              />
            </div>
          )}

          {mode === 'entities' && (
            <div>
              <Label htmlFor="entities">Entity Names</Label>
              <Input
                id="entities"
                placeholder="Comma-separated: Goldman Sachs, Federal Reserve, ..."
                value={entities}
                onChange={(e) => setEntities(e.target.value)}
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Enter entity names (not IDs) separated by commas
              </p>
            </div>
          )}

          {mode === 'text' && (
            <div>
              <Label htmlFor="text">Text Content</Label>
              <Textarea
                id="text"
                placeholder="Paste text content to analyze for risk (min. 10 characters)..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="mt-1 min-h-[100px]"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {text.length} characters {text.length > 0 && text.length < 10 && '(min. 10 required)'}
              </p>
            </div>
          )}

          <div className="flex items-center space-x-2">
            <Switch
              id="includeFactors"
              checked={includeFactors}
              onCheckedChange={setIncludeFactors}
            />
            <Label htmlFor="includeFactors">Include factor breakdown</Label>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            onClick={handleCalculate}
            disabled={isPending || !canCalculate()}
            className="flex-1"
          >
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Calculating...
              </>
            ) : (
              <>
                <Calculator className="mr-2 h-4 w-4" />
                Calculate Risk
              </>
            )}
          </Button>
          <Button variant="outline" onClick={handleClear}>
            Clear
          </Button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-lg">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error.message}</span>
          </div>
        )}

        {/* Results Section */}
        {data && (
          <div className="space-y-4 pt-4 border-t">
            {/* Risk Score Display */}
            <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
              <div>
                <p className="text-sm text-muted-foreground">Risk Score</p>
                <div className="flex items-center gap-2">
                  <p className={`text-3xl font-bold ${getRiskTextColor(data.risk_level)}`}>
                    {data.risk_score.toFixed(1)}
                  </p>
                  {data.risk_delta !== null && data.risk_delta !== undefined && (
                    <div className="flex items-center gap-1">
                      {data.risk_delta > 0 ? (
                        <TrendingUp className="h-4 w-4 text-red-500" />
                      ) : data.risk_delta < 0 ? (
                        <TrendingDown className="h-4 w-4 text-green-500" />
                      ) : (
                        <Minus className="h-4 w-4 text-gray-500" />
                      )}
                      <span className={`text-sm ${data.risk_delta > 0 ? 'text-red-500' : data.risk_delta < 0 ? 'text-green-500' : 'text-gray-500'}`}>
                        {data.risk_delta > 0 ? '+' : ''}{data.risk_delta.toFixed(1)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
              <Badge className={`${getRiskColor(data.risk_level)} text-white`}>
                {data.risk_level.toUpperCase()}
              </Badge>
            </div>

            {/* Cluster ID if present */}
            {data.cluster_id && (
              <div className="p-3 bg-blue-500/10 rounded-lg">
                <span className="text-sm">
                  Associated Cluster: <code className="bg-muted px-1 rounded">{data.cluster_id}</code>
                </span>
              </div>
            )}

            {/* Contributing Factors */}
            {data.factors && data.factors.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Contributing Factors</h4>
                <div className="space-y-2">
                  {data.factors.map((factor, i) => (
                    <div key={i} className="flex items-center justify-between p-2 bg-muted/50 rounded">
                      <span className="text-sm">{factor.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          Weight: {(factor.weight * 100).toFixed(0)}%
                        </span>
                        <Badge variant="outline">
                          +{factor.contribution.toFixed(1)}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamp */}
            <p className="text-xs text-muted-foreground text-right">
              Calculated: {new Date(data.timestamp).toLocaleString('de-DE')}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default RiskCalculationPanel;
