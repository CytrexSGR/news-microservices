/**
 * ML Lab Live Inference Tab
 *
 * Real-time gate predictions and trading decisions.
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
  Activity,
  RefreshCw,
  Play,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Zap,
  Eye,
  Clock,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { liveInferenceApi } from '../../api/mlLabApi';
import { MLArea, type LiveStatusResponse, type LiveInferenceResponse } from '../../types';
import {
  AREA_ICONS,
  SYMBOLS,
  TIMEFRAMES,
  PREDICTION_COLORS,
  ACTION_LABELS,
  ACTION_COLORS,
} from '../../utils/constants';

export function LiveInferenceTab() {
  const [status, setStatus] = useState<LiveStatusResponse | null>(null);
  const [lastPrediction, setLastPrediction] = useState<LiveInferenceResponse | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState('XRPUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1min');
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await liveInferenceApi.getStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch live status:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const runPrediction = async () => {
    setPredicting(true);
    try {
      const result = await liveInferenceApi.predict({
        symbol: selectedSymbol,
        timeframe: selectedTimeframe,
        include_decision: true,
      });
      setLastPrediction(result);
      toast.success(`Prediction completed in ${result.latency_ms}ms`);
    } catch (error) {
      console.error('Prediction failed:', error);
      toast.error('Prediction failed');
    } finally {
      setPredicting(false);
    }
  };

  const handleReloadModels = async () => {
    try {
      const result = await liveInferenceApi.reloadModels();
      toast.success(`Reloaded ${result.models_loaded} models`);
      fetchStatus();
    } catch (error) {
      toast.error('Failed to reload models');
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(runPrediction, 10000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, selectedSymbol, selectedTimeframe]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Live Inference Status
          </CardTitle>
          <CardDescription>Gate models loaded and ready for predictions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              {status?.status === 'ready' ? (
                <Badge className="bg-green-500">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Ready
                </Badge>
              ) : status?.status === 'loading' ? (
                <Badge className="bg-yellow-500">
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  Loading
                </Badge>
              ) : (
                <Badge className="bg-red-500">
                  <XCircle className="h-3 w-3 mr-1" />
                  Error
                </Badge>
              )}
              <span className="text-sm text-muted-foreground">
                {status?.total_models_loaded || 0} models loaded
              </span>
            </div>
            <Button variant="outline" size="sm" onClick={handleReloadModels}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Reload Models
            </Button>
          </div>

          {/* Gate Status Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {Object.values(MLArea).map((area) => {
              const gate = status?.gates?.[area];
              const isLoaded = gate?.model_loaded;
              return (
                <div
                  key={area}
                  className={`flex flex-col items-center p-3 rounded-lg ${
                    isLoaded ? 'bg-green-500/10 border border-green-500/30' : 'bg-muted'
                  }`}
                >
                  {AREA_ICONS[area]}
                  <span className="mt-1 text-xs font-medium capitalize">{area}</span>
                  {isLoaded ? (
                    <CheckCircle2 className="h-3 w-3 text-green-500 mt-1" />
                  ) : (
                    <XCircle className="h-3 w-3 text-gray-400 mt-1" />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Prediction Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Run Prediction
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Symbol:</label>
              <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SYMBOLS.map((s) => (
                    <SelectItem key={s.value} value={s.value}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Timeframe:</label>
              <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIMEFRAMES.map((tf) => (
                    <SelectItem key={tf.value} value={tf.value}>
                      {tf.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button onClick={runPrediction} disabled={predicting || status?.status !== 'ready'}>
              {predicting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              Run Prediction
            </Button>

            <Button
              variant={autoRefresh ? 'default' : 'outline'}
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              <Eye className="h-4 w-4 mr-2" />
              {autoRefresh ? 'Stop Auto' : 'Auto Refresh'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Last Prediction Result */}
      {lastPrediction && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Prediction Result
              </span>
              <span className="text-sm font-normal text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {lastPrediction.latency_ms}ms
              </span>
            </CardTitle>
            <CardDescription>
              {lastPrediction.symbol} | {lastPrediction.timeframe} |{' '}
              {new Date(lastPrediction.timestamp).toLocaleString()}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Trading Decision */}
            {lastPrediction.decision && (
              <div
                className={`p-4 rounded-lg ${ACTION_COLORS[lastPrediction.decision.action] || 'bg-muted'}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-lg font-bold">
                      {ACTION_LABELS[lastPrediction.decision.action] ||
                        lastPrediction.decision.action}
                    </p>
                    <p className="text-sm opacity-80">{lastPrediction.decision.reasoning}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold">
                      {(lastPrediction.decision.confidence * 100).toFixed(1)}%
                    </p>
                    <p className="text-xs opacity-60">Confidence</p>
                  </div>
                </div>
              </div>
            )}

            {/* Gate Results */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(lastPrediction.gates).map(([gate, result]) => (
                <div key={gate} className="p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    {AREA_ICONS[gate as MLArea]}
                    <span className="font-medium capitalize">{gate}</span>
                  </div>
                  {result.error ? (
                    <Alert variant="destructive" className="py-1 px-2">
                      <AlertTriangle className="h-3 w-3" />
                      <AlertDescription className="text-xs">{result.error}</AlertDescription>
                    </Alert>
                  ) : (
                    <>
                      <p
                        className={`text-lg font-bold capitalize ${PREDICTION_COLORS[result.prediction] || ''}`}
                      >
                        {result.prediction}
                      </p>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-muted-foreground">
                          Confidence: {(result.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No prediction yet */}
      {!lastPrediction && !predicting && (
        <Card>
          <CardContent className="py-12 text-center">
            <Zap className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No predictions yet</p>
            <p className="text-muted-foreground">
              Select a symbol and timeframe, then click "Run Prediction"
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default LiveInferenceTab;
