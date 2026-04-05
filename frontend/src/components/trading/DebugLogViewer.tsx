import { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle
} from '@/components/ui/Card';
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
import { ChevronDown, ChevronRight } from 'lucide-react';

interface DebugLog {
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

interface DebugLogViewerProps {
  logs: DebugLog[];
}

export const DebugLogViewer: React.FC<DebugLogViewerProps> = ({ logs }) => {
  const [filterEventType, setFilterEventType] = useState<string>('all');
  const [filterDecision, setFilterDecision] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  // Filter logs
  const filteredLogs = logs.filter(log => {
    if (filterEventType !== 'all' && log.event_type !== filterEventType) return false;
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

  const getEventTypeBadgeColor = (eventType: string) => {
    switch (eventType) {
      case 'entry_signal':
        return 'bg-blue-500 hover:bg-blue-600';
      case 'exit_signal':
        return 'bg-purple-500 hover:bg-purple-600';
      case 'trade_execution':
        return 'bg-green-500 hover:bg-green-600';
      case 'risk_check':
        return 'bg-orange-500 hover:bg-orange-600';
      default:
        return 'bg-gray-500 hover:bg-gray-600';
    }
  };

  const getDecisionBadgeColor = (decision: string) => {
    switch (decision) {
      case 'accepted':
        return 'bg-green-500 hover:bg-green-600';
      case 'rejected':
        return 'bg-red-500 hover:bg-red-600';
      case 'executed':
        return 'bg-blue-500 hover:bg-blue-600';
      case 'skipped':
        return 'bg-gray-500 hover:bg-gray-600';
      default:
        return 'bg-gray-500 hover:bg-gray-600';
    }
  };

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle>
          Debug Logs ({filteredLogs.length} / {logs.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="mb-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Select value={filterEventType} onValueChange={setFilterEventType}>
              <SelectTrigger>
                <SelectValue placeholder="Event Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Events</SelectItem>
                <SelectItem value="entry_signal">Entry Signals</SelectItem>
                <SelectItem value="exit_signal">Exit Signals</SelectItem>
                <SelectItem value="trade_execution">Trade Execution</SelectItem>
                <SelectItem value="risk_check">Risk Checks</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Select value={filterDecision} onValueChange={setFilterDecision}>
              <SelectTrigger>
                <SelectValue placeholder="Decision" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Decisions</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="executed">Executed</SelectItem>
                <SelectItem value="skipped">Skipped</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Input
              placeholder="Search reasons..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Logs table */}
        <div className="border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12"></TableHead>
                <TableHead>Time</TableHead>
                <TableHead>Event</TableHead>
                <TableHead>Signal</TableHead>
                <TableHead>Decision</TableHead>
                <TableHead>Reason</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                    No logs match the current filters
                  </TableCell>
                </TableRow>
              ) : (
                <>
                  {filteredLogs.map((log, idx) => {
                    const isExpanded = expandedRows.has(idx);
                    return (
                      <>
                        <TableRow key={`row-${idx}`} className="hover:bg-muted/50">
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleRow(idx)}
                              className="p-1 h-auto"
                            >
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </Button>
                          </TableCell>
                          <TableCell className="text-sm">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </TableCell>
                          <TableCell>
                            <Badge className={getEventTypeBadgeColor(log.event_type)}>
                              {log.event_type.replace('_', ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {log.signal_strength !== undefined && (
                              <div className="text-sm">
                                <span className="font-semibold">
                                  {(log.signal_strength * 100).toFixed(0)}%
                                </span>
                                {log.threshold && (
                                  <span className="text-muted-foreground ml-1">
                                    (threshold: {(log.threshold * 100).toFixed(0)}%)
                                  </span>
                                )}
                              </div>
                            )}
                          </TableCell>
                          <TableCell>
                            <Badge className={getDecisionBadgeColor(log.decision)}>
                              {log.decision}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm max-w-md truncate">
                            {log.reason}
                          </TableCell>
                        </TableRow>
                        {isExpanded && (
                          <TableRow key={`details-${idx}`}>
                            <TableCell colSpan={6} className="bg-muted/30 p-4">
                              <div className="space-y-4">
                                {/* Conditions Met */}
                                {log.conditions_met.length > 0 && (
                                  <div>
                                    <h4 className="text-sm font-semibold mb-2">Conditions Met:</h4>
                                    <div className="flex flex-wrap gap-2">
                                      {log.conditions_met.map((cond, i) => (
                                        <Badge key={i} variant="outline" className="bg-green-50 border-green-300 text-green-700">
                                          ✓ {cond}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Conditions Failed */}
                                {log.conditions_failed.length > 0 && (
                                  <div>
                                    <h4 className="text-sm font-semibold mb-2">Conditions Failed:</h4>
                                    <div className="flex flex-wrap gap-2">
                                      {log.conditions_failed.map((cond, i) => (
                                        <Badge key={i} variant="outline" className="bg-red-50 border-red-300 text-red-700">
                                          ✗ {cond}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Full Reason */}
                                <div>
                                  <h4 className="text-sm font-semibold mb-2">Full Reason:</h4>
                                  <p className="text-sm text-muted-foreground bg-background p-2 rounded border">
                                    {log.reason}
                                  </p>
                                </div>

                                {/* Indicators */}
                                {Object.keys(log.indicators).length > 0 && (
                                  <div>
                                    <h4 className="text-sm font-semibold mb-2">Indicators:</h4>
                                    <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
                                      {JSON.stringify(log.indicators, null, 2)}
                                    </pre>
                                  </div>
                                )}

                                {/* Parameters */}
                                {log.parameters && Object.keys(log.parameters).length > 0 && (
                                  <div>
                                    <h4 className="text-sm font-semibold mb-2">Parameters:</h4>
                                    <pre className="text-xs bg-background p-2 rounded border overflow-x-auto">
                                      {JSON.stringify(log.parameters, null, 2)}
                                    </pre>
                                  </div>
                                )}

                                {/* Price */}
                                {log.price !== undefined && (
                                  <div>
                                    <h4 className="text-sm font-semibold mb-2">Price:</h4>
                                    <p className="text-sm font-mono">${log.price.toFixed(2)}</p>
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
      </CardContent>
    </Card>
  );
};
