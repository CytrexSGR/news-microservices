/**
 * ConditionTimeline Component
 *
 * Tab 1 of the Strategy Debugger: Detailed condition-by-condition breakdown.
 * Shows each candle evaluation with expandable details for all conditions,
 * indicators, and decision reasons.
 */

import { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, Clock } from 'lucide-react';

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

export interface ConditionTimelineProps {
  logs: DebugLog[];
}

export const ConditionTimeline: React.FC<ConditionTimelineProps> = ({ logs }) => {
  const [filterDecision, setFilterDecision] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  // Filter logs
  const filteredLogs = logs.filter(log => {
    if (filterDecision !== 'all' && log.decision !== filterDecision) return false;
    if (searchTerm && !log.reason.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  const getDecisionBadgeColor = (decision: string) => {
    switch (decision) {
      case 'accepted':
        return 'bg-green-500 hover:bg-green-600 text-white';
      case 'rejected':
        return 'bg-red-500 hover:bg-red-600 text-white';
      default:
        return 'bg-gray-500 hover:bg-gray-600 text-white';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Select value={filterDecision} onValueChange={setFilterDecision}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by decision" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Decisions</SelectItem>
              <SelectItem value="accepted">✅ Accepted</SelectItem>
              <SelectItem value="rejected">❌ Rejected</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Input
            placeholder="Search in reason text..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Results Count */}
      <div className="text-sm text-muted-foreground">
        Showing {filteredLogs.length} of {logs.length} candles
      </div>

      {/* Timeline Table */}
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12"></TableHead>
              <TableHead className="w-48">Timestamp</TableHead>
              <TableHead className="w-32">Price</TableHead>
              <TableHead className="w-24">Signal</TableHead>
              <TableHead className="w-32">Decision</TableHead>
              <TableHead>Reason</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredLogs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                  No candles match the current filters
                </TableCell>
              </TableRow>
            ) : (
              <>
                {filteredLogs.map((log, idx) => {
                  const isExpanded = expandedRows.has(idx);
                  const totalConditions = log.conditions_met.length + log.conditions_failed.length;
                  const passedConditions = log.conditions_met.length;

                  return (
                    <>
                      {/* Main Row */}
                      <TableRow
                        key={`row-${idx}`}
                        className="hover:bg-muted/50 cursor-pointer"
                        onClick={() => toggleRow(idx)}
                      >
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="p-1 h-auto"
                          >
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </Button>
                        </TableCell>
                        <TableCell className="text-sm font-mono">
                          {formatTimestamp(log.timestamp)}
                        </TableCell>
                        <TableCell className="text-sm font-semibold">
                          ${log.price?.toFixed(2) || 'N/A'}
                        </TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <span className={`font-semibold ${passedConditions === totalConditions ? 'text-green-600' : 'text-red-600'}`}>
                              {passedConditions}/{totalConditions}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={getDecisionBadgeColor(log.decision)}>
                            {log.decision === 'accepted' ? '✅ ENTRY' : '❌ NO ENTRY'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm max-w-md truncate">
                          {log.reason}
                        </TableCell>
                      </TableRow>

                      {/* Expanded Details Row */}
                      {isExpanded && (
                        <TableRow key={`details-${idx}`}>
                          <TableCell colSpan={6} className="bg-muted/30 p-6">
                            <div className="space-y-6">
                              {/* Header: Candle Info */}
                              <div className="pb-4 border-b">
                                <h3 className="text-lg font-semibold flex items-center gap-2">
                                  <Clock className="h-5 w-5" />
                                  Candle {idx + 1}: {formatTimestamp(log.timestamp)}
                                </h3>
                                <p className="text-sm text-muted-foreground mt-1">
                                  Price: <span className="font-mono font-semibold">${log.price?.toFixed(2)}</span>
                                  {' • '}
                                  Signal Strength: <span className="font-semibold">{((log.signal_strength || 0) * 100).toFixed(0)}%</span>
                                </p>
                              </div>

                              {/* Conditions Met */}
                              {log.conditions_met.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-green-700">
                                    <CheckCircle2 className="h-4 w-4" />
                                    Conditions Met ({log.conditions_met.length})
                                  </h4>
                                  <div className="space-y-2">
                                    {log.conditions_met.map((cond, i) => (
                                      <div
                                        key={i}
                                        className="flex items-start gap-2 p-3 bg-green-50 border border-green-200 rounded-lg"
                                      >
                                        <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                                        <span className="text-sm font-mono text-green-900">{cond}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Conditions Failed */}
                              {log.conditions_failed.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-2 text-red-700">
                                    <XCircle className="h-4 w-4" />
                                    Conditions Failed ({log.conditions_failed.length})
                                  </h4>
                                  <div className="space-y-2">
                                    {log.conditions_failed.map((cond, i) => (
                                      <div
                                        key={i}
                                        className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg"
                                      >
                                        <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                                        <span className="text-sm font-mono text-red-900">{cond}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Full Reason */}
                              <div>
                                <h4 className="text-sm font-semibold mb-2">Decision Reason:</h4>
                                <div className="p-3 bg-background border rounded-lg">
                                  <p className="text-sm text-muted-foreground">{log.reason}</p>
                                </div>
                              </div>

                              {/* Indicators */}
                              {Object.keys(log.indicators).length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold mb-2">Indicator Values:</h4>
                                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                    {Object.entries(log.indicators).map(([key, value]) => (
                                      <div key={key} className="p-2 bg-background border rounded">
                                        <div className="text-xs text-muted-foreground">{key}</div>
                                        <div className="text-sm font-mono font-semibold">
                                          {typeof value === 'number' ? value.toFixed(2) : String(value)}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Parameters (if available) */}
                              {log.parameters && Object.keys(log.parameters).length > 0 && (
                                <div>
                                  <h4 className="text-sm font-semibold mb-2">Strategy Parameters:</h4>
                                  <pre className="text-xs bg-background p-3 rounded border overflow-x-auto">
                                    {JSON.stringify(log.parameters, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </>
                  );
                })}
              </>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};
