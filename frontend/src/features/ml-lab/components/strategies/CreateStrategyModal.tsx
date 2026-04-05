/**
 * Create Strategy Modal
 *
 * Modal for creating a new trading strategy with portfolio configuration.
 */

import { useState } from 'react';
import { X, Plus, Trash2, Percent, DollarSign, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Switch } from '@/components/ui/Switch';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Slider } from '@/components/ui/slider';
import toast from 'react-hot-toast';

import { tradingStrategyApi } from '../../api/mlLabApi';
import type { TradingStrategyCreate } from '../../types';

// Available symbols for trading
const AVAILABLE_SYMBOLS = [
  'BTCUSDT',
  'ETHUSDT',
  'XRPUSDT',
  'SOLUSDT',
  'ADAUSDT',
  'DOGEUSDT',
  'LINKUSDT',
  'AVAXUSDT',
  'MATICUSDT',
  'DOTUSDT',
];

// Available timeframes
const TIMEFRAMES = ['1min', '5min', '15min', '30min', '1h', '4h', '1d'];

interface CreateStrategyModalProps {
  onClose: () => void;
  onCreated: () => void;
}

export function CreateStrategyModal({ onClose, onCreated }: CreateStrategyModalProps) {
  const [loading, setLoading] = useState(false);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [symbols, setSymbols] = useState<string[]>(['BTCUSDT', 'ETHUSDT']);
  const [allocations, setAllocations] = useState<Record<string, number>>({
    BTCUSDT: 50,
    ETHUSDT: 50,
  });
  const [totalCapital, setTotalCapital] = useState(10000);
  const [positionSizePct, setPositionSizePct] = useState(10);
  const [stopLossPct, setStopLossPct] = useState(2);
  const [takeProfitPct, setTakeProfitPct] = useState(4);
  const [maxPositions, setMaxPositions] = useState(3);
  const [timeframe, setTimeframe] = useState('5min');
  const [mlGatesEnabled, setMlGatesEnabled] = useState(true);

  const addSymbol = (symbol: string) => {
    if (!symbols.includes(symbol)) {
      const newSymbols = [...symbols, symbol];
      setSymbols(newSymbols);
      // Recalculate allocations equally
      const equalAlloc = 100 / newSymbols.length;
      const newAllocations: Record<string, number> = {};
      newSymbols.forEach((s) => {
        newAllocations[s] = equalAlloc;
      });
      setAllocations(newAllocations);
    }
  };

  const removeSymbol = (symbol: string) => {
    if (symbols.length <= 1) {
      toast.error('At least one symbol is required');
      return;
    }
    const newSymbols = symbols.filter((s) => s !== symbol);
    setSymbols(newSymbols);
    // Recalculate allocations equally
    const equalAlloc = 100 / newSymbols.length;
    const newAllocations: Record<string, number> = {};
    newSymbols.forEach((s) => {
      newAllocations[s] = equalAlloc;
    });
    setAllocations(newAllocations);
  };

  const updateAllocation = (symbol: string, value: number) => {
    const newAllocations = { ...allocations, [symbol]: value };
    setAllocations(newAllocations);
  };

  const totalAllocation = Object.values(allocations).reduce((sum, v) => sum + v, 0);
  const isAllocationValid = Math.abs(totalAllocation - 100) < 0.01;

  const handleSubmit = async () => {
    if (!name.trim()) {
      toast.error('Strategy name is required');
      return;
    }
    if (symbols.length === 0) {
      toast.error('At least one symbol is required');
      return;
    }
    if (!isAllocationValid) {
      toast.error('Allocations must sum to 100%');
      return;
    }

    setLoading(true);
    try {
      // Convert allocations from percentages to decimals
      const allocationDecimals: Record<string, number> = {};
      Object.entries(allocations).forEach(([symbol, pct]) => {
        allocationDecimals[symbol] = pct / 100;
      });

      const data: TradingStrategyCreate = {
        name: name.trim(),
        description: description.trim() || undefined,
        symbols,
        allocations: allocationDecimals,
        total_capital: totalCapital,
        position_size_pct: positionSizePct,
        stop_loss_pct: stopLossPct,
        take_profit_pct: takeProfitPct,
        max_positions: maxPositions,
        timeframe,
        ml_gates_enabled: mlGatesEnabled,
      };

      await tradingStrategyApi.create(data);
      toast.success('Strategy created successfully');
      onCreated();
    } catch (error: any) {
      console.error('Failed to create strategy:', error);
      toast.error(error.response?.data?.detail || 'Failed to create strategy');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-background border rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">Create Trading Strategy</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Strategy Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Multi-Coin Momentum"
              />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your strategy..."
                rows={2}
              />
            </div>
          </div>

          {/* Symbols & Allocations */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Symbols & Allocation</Label>
              <Select onValueChange={addSymbol}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Add symbol" />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_SYMBOLS.filter((s) => !symbols.includes(s)).map((symbol) => (
                    <SelectItem key={symbol} value={symbol}>
                      {symbol}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              {symbols.map((symbol) => (
                <div key={symbol} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                  <Badge variant="outline" className="font-mono">
                    {symbol}
                  </Badge>
                  <div className="flex-1">
                    <Slider
                      value={[allocations[symbol] || 0]}
                      onValueChange={([value]) => updateAllocation(symbol, value)}
                      min={0}
                      max={100}
                      step={1}
                    />
                  </div>
                  <div className="w-16 text-right font-mono">
                    {(allocations[symbol] || 0).toFixed(0)}%
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeSymbol(symbol)}
                    className="text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>

            <div className={`flex items-center gap-2 text-sm ${isAllocationValid ? 'text-green-600' : 'text-destructive'}`}>
              {!isAllocationValid && <AlertTriangle className="h-4 w-4" />}
              <span>
                Total: {totalAllocation.toFixed(0)}%
                {!isAllocationValid && ' (must be 100%)'}
              </span>
            </div>
          </div>

          {/* Capital & Position Size */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="capital">Total Capital</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="capital"
                  type="number"
                  value={totalCapital}
                  onChange={(e) => setTotalCapital(Number(e.target.value))}
                  className="pl-9"
                  min={100}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="positionSize">Position Size</Label>
              <div className="relative">
                <Percent className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  id="positionSize"
                  type="number"
                  value={positionSizePct}
                  onChange={(e) => setPositionSizePct(Number(e.target.value))}
                  className="pl-9"
                  min={1}
                  max={100}
                />
              </div>
            </div>
          </div>

          {/* Risk Management */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="stopLoss">Stop Loss %</Label>
              <Input
                id="stopLoss"
                type="number"
                value={stopLossPct}
                onChange={(e) => setStopLossPct(Number(e.target.value))}
                min={0.1}
                max={50}
                step={0.1}
              />
            </div>
            <div>
              <Label htmlFor="takeProfit">Take Profit %</Label>
              <Input
                id="takeProfit"
                type="number"
                value={takeProfitPct}
                onChange={(e) => setTakeProfitPct(Number(e.target.value))}
                min={0.1}
                max={100}
                step={0.1}
              />
            </div>
            <div>
              <Label htmlFor="maxPositions">Max Positions</Label>
              <Input
                id="maxPositions"
                type="number"
                value={maxPositions}
                onChange={(e) => setMaxPositions(Number(e.target.value))}
                min={1}
                max={20}
              />
            </div>
          </div>

          {/* Timeframe & ML Gates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="timeframe">Timeframe</Label>
              <Select value={timeframe} onValueChange={setTimeframe}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TIMEFRAMES.map((tf) => (
                    <SelectItem key={tf} value={tf}>
                      {tf}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
              <div>
                <Label>ML Gates</Label>
                <p className="text-xs text-muted-foreground">Use ML models for trade validation</p>
              </div>
              <Switch
                checked={mlGatesEnabled}
                onCheckedChange={setMlGatesEnabled}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 p-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading || !isAllocationValid}>
            {loading ? 'Creating...' : 'Create Strategy'}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default CreateStrategyModal;
