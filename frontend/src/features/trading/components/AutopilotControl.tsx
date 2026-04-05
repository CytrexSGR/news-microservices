/**
 * Autopilot Control - Signal Generator Control Widget
 *
 * Displays and controls the automated trading signal generator:
 * - Current status (active/paused)
 * - Next scan countdown
 * - Monitored trading pairs
 * - Enable/disable toggle
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { predictionAPI } from '@/api/predictionService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/Switch';
import { RefreshCw, Bot, Clock } from 'lucide-react';
import toast from 'react-hot-toast';
import { useEffect, useState } from 'react';

export function AutopilotControl() {
  const queryClient = useQueryClient();
  const [countdown, setCountdown] = useState<string>('--:--:--');

  // Fetch scheduler status
  const { data: status, isLoading } = useQuery({
    queryKey: ['scheduler-status'],
    queryFn: () => predictionAPI.getSchedulerStatus(),
    refetchInterval: 5000, // Poll every 5 seconds
  });

  // Toggle mutation
  const toggleMutation = useMutation({
    mutationFn: (enable: boolean) => predictionAPI.toggleAutotrade(enable),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['scheduler-status'] });
      toast.success(data.message);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to toggle auto-trading');
    },
  });

  // Calculate countdown to next scan
  useEffect(() => {
    if (!status?.next_run) {
      setCountdown('Paused');
      return;
    }

    const updateCountdown = () => {
      const nextRun = new Date(status.next_run!);
      const now = new Date();
      const diff = nextRun.getTime() - now.getTime();

      if (diff <= 0) {
        setCountdown('Scanning...');
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      setCountdown(
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      );
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [status?.next_run]);

  const isActive = status?.running && status?.next_run !== null;

  if (isLoading) {
    return (
      <Card className="bg-[#1A1F2E] border-gray-800">
        <CardContent className="flex items-center justify-center p-8">
          <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-[#1A1F2E] border-gray-800 hover:bg-[#1F2937] transition-colors">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className={`h-5 w-5 ${isActive ? 'text-green-500' : 'text-gray-400'}`} />
            <CardTitle className="text-white">Signal Generator</CardTitle>
            <div className={`h-2 w-2 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
          </div>
          <Switch
            checked={status?.enabled && status?.running}
            onCheckedChange={(checked) => toggleMutation.mutate(checked)}
            disabled={toggleMutation.isPending || !status?.enabled}
          />
        </div>
        <CardDescription className="text-gray-400">
          {status?.strategy || 'OI_Trend'} - {status?.interval_minutes || 60} min interval
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Next Scan Countdown */}
        <div className="flex items-center gap-3 p-3 bg-[#131823] rounded-lg">
          <Clock className="h-4 w-4 text-gray-400" />
          <div className="flex-1">
            <p className="text-xs text-gray-400 mb-1">Next Scan</p>
            <p className={`text-lg font-mono font-bold ${isActive ? 'text-green-500' : 'text-gray-500'}`}>
              {countdown}
            </p>
          </div>
        </div>

        {/* Monitored Pairs */}
        <div>
          <p className="text-xs text-gray-400 mb-2">Monitored Pairs</p>
          <div className="flex flex-wrap gap-2">
            {(status?.trading_pairs || []).map((pair) => (
              <Badge
                key={pair}
                variant="outline"
                className="text-xs bg-[#131823] border-gray-700 text-gray-300"
              >
                {pair}
              </Badge>
            ))}
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-800">
          <span className="text-xs text-gray-400">Status</span>
          <Badge
            variant={isActive ? 'default' : 'secondary'}
            className={isActive ? 'bg-green-500/20 text-green-500 border-green-500/30' : 'bg-gray-500/20 text-gray-400 border-gray-500/30'}
          >
            {isActive ? 'Active' : 'Paused'}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
