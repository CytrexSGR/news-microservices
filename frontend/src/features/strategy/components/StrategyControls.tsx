/**
 * StrategyControls Component
 *
 * Controls for symbol/timeframe selection and actions
 */

import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TrendingUp, Clock, Activity } from 'lucide-react';
import type { Timeframe } from '@/types/indicators';
import { AVAILABLE_TIMEFRAMES, TIMEFRAME_LABELS } from '@/types/indicators';
import { BYBIT_SYMBOLS } from '@/constants/symbols';

interface StrategyControlsProps {
  strategyId: string;
  selectedSymbol: string;
  selectedTimeframe: Timeframe;
  onSymbolChange: (symbol: string) => void;
  onTimeframeChange: (timeframe: Timeframe) => void;
  showDebugButton?: boolean;
}

export function StrategyControls({
  strategyId,
  selectedSymbol,
  selectedTimeframe,
  onSymbolChange,
  onTimeframeChange,
  showDebugButton = true,
}: StrategyControlsProps) {
  const navigate = useNavigate();

  return (
    <div className="flex items-center gap-3 flex-wrap">
      {/* Symbol Selector */}
      <div className="flex items-center gap-2">
        <TrendingUp className="h-4 w-4 text-muted-foreground" />
        <Select value={selectedSymbol} onValueChange={onSymbolChange}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Select symbol" />
          </SelectTrigger>
          <SelectContent>
            {BYBIT_SYMBOLS.map((s) => (
              <SelectItem key={s.symbol} value={s.symbol}>
                {s.base}/USDT
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Timeframe Selector */}
      <div className="flex items-center gap-2">
        <Clock className="h-4 w-4 text-muted-foreground" />
        <Select
          value={selectedTimeframe}
          onValueChange={(value) => onTimeframeChange(value as Timeframe)}
        >
          <SelectTrigger className="w-[100px]">
            <SelectValue placeholder="Timeframe" />
          </SelectTrigger>
          <SelectContent>
            {AVAILABLE_TIMEFRAMES.map((tf) => (
              <SelectItem key={tf} value={tf}>
                {TIMEFRAME_LABELS[tf]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {showDebugButton && (
        <Button onClick={() => navigate(`/trading/debug?strategy=${strategyId}`)}>
          <Activity className="mr-2 h-4 w-4" />
          Run Debug
        </Button>
      )}
    </div>
  );
}
