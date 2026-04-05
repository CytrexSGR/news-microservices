import type { IndicatorsSnapshot } from '@/types/indicators';

interface LegacyRegimeFallbackProps {
  liveIndicators: IndicatorsSnapshot;
}

export function LegacyRegimeFallback({ liveIndicators }: LegacyRegimeFallbackProps) {
  return (
    <div className="mt-3 p-3 bg-muted/50 rounded-lg">
      <p className="text-xs text-muted-foreground">
        Legacy 2-Indicator Mode (comprehensive=false)
      </p>
      <div className="mt-2 space-y-1">
        {liveIndicators.adx && (
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">ADX:</span>
            <span className="font-mono">{liveIndicators.adx.adx?.toFixed(2) ?? 'N/A'}</span>
          </div>
        )}
        {liveIndicators.bbw !== undefined && (
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">BBW:</span>
            <span className="font-mono">{liveIndicators.bbw.toFixed(4)}</span>
          </div>
        )}
      </div>
    </div>
  );
}
