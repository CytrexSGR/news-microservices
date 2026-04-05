/**
 * Positions Table - Live open positions display
 *
 * Shows active positions with:
 * - Symbol, Side (Long/Short)
 * - Entry price, Current price
 * - Unrealized P&L (color-coded)
 * - Actions (close position)
 */

import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/Button'
import { X, Loader2 } from 'lucide-react'
import { useOpenPositions, useClosePosition } from '@/hooks/useTrading'
import type { Position } from '@/lib/api/trading'

export function PositionsTable() {
  const { data, isLoading, error } = useOpenPositions()
  const closePosition = useClosePosition()

  const positions = data?.positions || []

  const handleClose = async (positionId: string) => {
    if (confirm('Close this position?')) {
      await closePosition.mutateAsync(positionId)
    }
  }

  return (
    <Card className="bg-[#1A1F2E] border-gray-800 p-6 h-full">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Open Positions</h2>
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-[#00D4FF]" />
        ) : (
          <Badge variant="outline" className="text-[#00D4FF] bg-[#00D4FF]/10">
            {positions.length} Active
          </Badge>
        )}
      </div>

      {error && (
        <div className="text-center py-12 text-red-400">
          <p>Failed to load positions</p>
          <p className="text-sm text-gray-500">{error.message}</p>
        </div>
      )}

      <div className="space-y-3">
        {positions.map((position: Position) => (
          <div
            key={position.id}
            className="bg-[#151922] border border-gray-800 rounded-lg p-4 hover:bg-[#1F2937] transition-colors"
          >
            {/* Header: Symbol + Side */}
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="font-bold">{position.symbol}</p>
                <Badge
                  variant="outline"
                  className={
                    position.side.toUpperCase() === 'LONG'
                      ? 'text-[#26A69A] bg-[#26A69A]/10'
                      : 'text-[#EF5350] bg-[#EF5350]/10'
                  }
                >
                  {position.side.toUpperCase()}
                </Badge>
              </div>

              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white"
                onClick={() => handleClose(position.id)}
                disabled={closePosition.isPending}
              >
                {closePosition.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <X className="w-4 h-4" />
                )}
              </Button>
            </div>

            {/* Prices */}
            <div className="grid grid-cols-2 gap-3 mb-3 text-sm">
              <div>
                <p className="text-gray-400">Entry</p>
                <p className="font-medium">${position.entry_price.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-gray-400">Stop Loss</p>
                <p className="font-medium">
                  {position.stop_loss
                    ? `$${position.stop_loss.toLocaleString()}`
                    : 'N/A'}
                </p>
              </div>
            </div>

            {/* Quantity + P&L */}
            <div className="flex items-center justify-between pt-3 border-t border-gray-800">
              <div className="text-sm">
                <p className="text-gray-400">Quantity</p>
                <p className="font-medium">{position.quantity.toFixed(4)}</p>
              </div>
              <div className="text-right">
                <p className="text-gray-400 text-sm">Unrealized P&L</p>
                <p
                  className={`font-bold ${
                    (position.unrealized_pnl || 0) >= 0
                      ? 'text-[#26A69A]'
                      : 'text-[#EF5350]'
                  }`}
                >
                  {(position.unrealized_pnl || 0) >= 0 ? '+' : ''}
                  ${(position.unrealized_pnl || 0).toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {!isLoading && !error && positions.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <p>No open positions</p>
        </div>
      )}
    </Card>
  )
}
