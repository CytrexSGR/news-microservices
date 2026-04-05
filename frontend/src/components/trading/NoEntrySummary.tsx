/**
 * NoEntrySummary Component
 *
 * Tab 2 of the Strategy Debugger: Summary analysis of why strategy didn't enter trades.
 * Analyzes all debug logs to identify:
 * - Most common failure reasons
 * - "Closest to entry" moments (highest signal strength)
 * - Overall statistics and patterns
 */

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { TrendingDown, AlertCircle, Target, Calendar } from 'lucide-react';

export interface DebugLog {
  timestamp: string;
  event_type: string;
  signal_strength?: number;
  threshold?: number;
  conditions_met: string[];
  conditions_failed: string[];
  decision: string;
  reason: string;
  price?: number;
  indicators: Record<string, any>;
  parameters: Record<string, any>;
}

export interface NoEntrySummaryProps {
  logs: DebugLog[];
}

interface FailureReason {
  reason: string;
  count: number;
  percentage: number;
  examples: DebugLog[];
}

export const NoEntrySummary: React.FC<NoEntrySummaryProps> = ({ logs }) => {
  // Calculate statistics
  const stats = useMemo(() => {
    const totalCandles = logs.length;
    const entriesAccepted = logs.filter(log => log.decision === 'accepted').length;
    const entriesRejected = logs.filter(log => log.decision === 'rejected').length;

    // Find closest to entry (highest signal strength among rejected)
    const rejectedLogs = logs.filter(log => log.decision === 'rejected');
    const closestToEntry = rejectedLogs.reduce<DebugLog | null>((best, log) => {
      if (!best || (log.signal_strength || 0) > (best.signal_strength || 0)) {
        return log;
      }
      return best;
    }, null);

    // Analyze failure reasons by parsing conditions_failed
    const failureReasons = new Map<string, { count: number; examples: DebugLog[] }>();

    rejectedLogs.forEach(log => {
      log.conditions_failed.forEach(condition => {
        // Extract the condition description (before the "→")
        const parts = condition.split('→');
        const conditionKey = parts[0]?.trim() || condition;

        if (!failureReasons.has(conditionKey)) {
          failureReasons.set(conditionKey, { count: 0, examples: [] });
        }

        const entry = failureReasons.get(conditionKey)!;
        entry.count++;
        if (entry.examples.length < 3) {
          entry.examples.push(log);
        }
      });
    });

    // Convert to array and sort by count
    const failureReasonsArray: FailureReason[] = Array.from(failureReasons.entries())
      .map(([reason, data]) => ({
        reason,
        count: data.count,
        percentage: (data.count / totalCandles) * 100,
        examples: data.examples
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5); // Top 5 reasons

    // Analyze regime distribution
    const regimeDistribution = new Map<string, number>();
    logs.forEach(log => {
      const regimeMatch = log.reason.match(/Regime: (\w+)/);
      if (regimeMatch) {
        const regime = regimeMatch[1];
        regimeDistribution.set(regime, (regimeDistribution.get(regime) || 0) + 1);
      }
    });

    return {
      totalCandles,
      entriesAccepted,
      entriesRejected,
      closestToEntry,
      failureReasons: failureReasonsArray,
      regimeDistribution: Array.from(regimeDistribution.entries())
        .map(([regime, count]) => ({
          regime,
          count,
          percentage: (count / totalCandles) * 100
        }))
        .sort((a, b) => b.count - a.count)
    };
  }, [logs]);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Overview Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Total Candles
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.totalCandles}</div>
            <p className="text-xs text-muted-foreground mt-1">Evaluated candles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-green-600">
              <Target className="h-4 w-4" />
              Entries Accepted
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{stats.entriesAccepted}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {((stats.entriesAccepted / stats.totalCandles) * 100).toFixed(1)}% of candles
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-red-600">
              <TrendingDown className="h-4 w-4" />
              Entries Rejected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{stats.entriesRejected}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {((stats.entriesRejected / stats.totalCandles) * 100).toFixed(1)}% of candles
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Closest to Entry */}
      {stats.closestToEntry && stats.entriesRejected > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-amber-500" />
              Closest to Entry
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Timestamp</p>
                  <p className="text-lg font-mono">{formatTimestamp(stats.closestToEntry.timestamp)}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">Signal Strength</p>
                  <p className="text-2xl font-bold text-amber-600">
                    {((stats.closestToEntry.signal_strength || 0) * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm font-medium mb-2">Why it failed:</p>
                <p className="text-sm text-muted-foreground">{stats.closestToEntry.reason}</p>
              </div>

              {stats.closestToEntry.conditions_failed.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Failed Conditions:</p>
                  <div className="space-y-1">
                    {stats.closestToEntry.conditions_failed.map((cond, idx) => (
                      <div key={idx} className="text-sm font-mono p-2 bg-red-50 border border-red-200 rounded">
                        {cond}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top Failure Reasons */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            Why No Entries? - Top Failure Reasons
          </CardTitle>
        </CardHeader>
        <CardContent>
          {stats.failureReasons.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No rejected entries to analyze</p>
            </div>
          ) : (
            <div className="space-y-4">
              {stats.failureReasons.map((failure, idx) => (
                <div key={idx} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono">
                          #{idx + 1}
                        </Badge>
                        <span className="text-sm font-medium">{failure.reason}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Failed in {failure.count} out of {stats.totalCandles} candles
                        ({failure.percentage.toFixed(1)}%)
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-2xl font-bold text-red-600">{failure.count}</p>
                      <p className="text-xs text-muted-foreground">failures</p>
                    </div>
                  </div>
                  <Progress value={failure.percentage} className="h-2" />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Regime Distribution */}
      {stats.regimeDistribution.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5" />
              Market Regime Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.regimeDistribution.map((regime, idx) => (
                <div key={idx} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge className="bg-blue-500 hover:bg-blue-600 text-white">
                          {regime.regime}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {regime.count} candles ({regime.percentage.toFixed(1)}%)
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      <p className="text-2xl font-bold">{regime.count}</p>
                    </div>
                  </div>
                  <Progress value={regime.percentage} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
