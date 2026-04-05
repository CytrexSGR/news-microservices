/**
 * StrategyCard Component
 *
 * Card component for displaying strategy summary in list view.
 * Shows name, version, description, regime count, and quick actions.
 */

import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/DropdownMenu';
import {
  Activity,
  Copy,
  Trash2,
  MoreVertical,
  PlayCircle,
  Settings,
  TrendingUp,
  Layers,
  Gauge,
} from 'lucide-react';
import type { Strategy } from '../types';

interface StrategyCardProps {
  strategy: Strategy;
  onClone?: (strategy: Strategy) => void;
  onDelete?: (strategy: Strategy) => void;
  isDeleting?: boolean;
}

export function StrategyCard({ strategy, onClone, onDelete, isDeleting }: StrategyCardProps) {
  const navigate = useNavigate();
  const def = strategy.definition;

  // Count regimes
  const regimeCount = def?.logic ? Object.keys(def.logic).length : 0;

  // Count indicators
  const indicatorCount = def?.indicators?.length || 0;

  // Get risk management info
  const hasRiskManagement = !!def?.riskManagement;
  const hasStopLoss = !!def?.riskManagement?.stopLoss;
  const hasTakeProfit = !!def?.riskManagement?.takeProfit;

  // Get MTFA info
  const hasMTFA = !!def?.multiTimeframeAnalysis;
  const mtfaTimeframes = def?.multiTimeframeAnalysis?.timeframes?.length || 0;

  return (
    <Card className="group hover:shadow-md transition-shadow cursor-pointer">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex-1" onClick={() => navigate(`/trading/strategy/${strategy.id}`)}>
            <div className="flex items-center gap-2 mb-1">
              <CardTitle className="text-lg group-hover:text-primary transition-colors">
                {def?.name || strategy.name || 'Unnamed Strategy'}
              </CardTitle>
              <Badge variant="secondary" className="text-xs">
                v{strategy.version}
              </Badge>
            </div>
            <CardDescription className="line-clamp-2">
              {def?.description || strategy.description || 'No description'}
            </CardDescription>
          </div>

          {/* Actions Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => navigate(`/trading/strategy/${strategy.id}`)}>
                <Settings className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate(`/trading/debug?strategy=${strategy.id}`)}>
                <Activity className="mr-2 h-4 w-4" />
                Debug Mode
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {onClone && (
                <DropdownMenuItem onClick={() => onClone(strategy)}>
                  <Copy className="mr-2 h-4 w-4" />
                  Clone Strategy
                </DropdownMenuItem>
              )}
              {onDelete && (
                <DropdownMenuItem
                  onClick={() => onDelete(strategy)}
                  className="text-destructive focus:text-destructive"
                  disabled={isDeleting}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent onClick={() => navigate(`/trading/strategy/${strategy.id}`)}>
        {/* Strategy Stats */}
        <div className="grid grid-cols-4 gap-3 text-sm">
          {/* Regimes */}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <TrendingUp className="h-4 w-4" />
            <span>{regimeCount} Regimes</span>
          </div>

          {/* Indicators */}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Gauge className="h-4 w-4" />
            <span>{indicatorCount} Indicators</span>
          </div>

          {/* MTFA */}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Layers className="h-4 w-4" />
            <span>{hasMTFA ? `${mtfaTimeframes} TFs` : 'No MTFA'}</span>
          </div>

          {/* Risk Management */}
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <PlayCircle className="h-4 w-4" />
            <span>
              {hasRiskManagement
                ? `${hasStopLoss ? 'SL' : ''}${hasStopLoss && hasTakeProfit ? '/' : ''}${hasTakeProfit ? 'TP' : ''}`
                : 'No Risk'}
            </span>
          </div>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex gap-2 mt-4 pt-3 border-t">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/trading/strategy/${strategy.id}`);
            }}
          >
            <Settings className="mr-2 h-3.5 w-3.5" />
            View
          </Button>
          <Button
            variant="default"
            size="sm"
            className="flex-1"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/trading/debug?strategy=${strategy.id}`);
            }}
          >
            <Activity className="mr-2 h-3.5 w-3.5" />
            Debug
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
