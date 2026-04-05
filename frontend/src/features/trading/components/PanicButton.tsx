/**
 * Panic Button - Emergency position close
 *
 * Red, glowing button to close ALL positions at once
 * Requires confirmation before execution
 */

import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { AlertCircle, Loader2 } from 'lucide-react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useCloseAllPositions } from '@/hooks/useTrading'

export function PanicButton() {
  const [showConfirm, setShowConfirm] = useState(false)
  const closeAll = useCloseAllPositions()

  const handlePanic = async () => {
    try {
      await closeAll.mutateAsync()
      console.log('✅ All positions closed successfully')
      setShowConfirm(false)
    } catch (error) {
      console.error('❌ Failed to close all positions:', error)
      alert('Failed to close positions. Check console for details.')
    }
  }

  return (
    <>
      <Button
        variant="destructive"
        size="lg"
        className="bg-[#EF5350] hover:bg-[#D32F2F] text-white font-bold shadow-lg shadow-red-500/50 animate-pulse"
        onClick={() => setShowConfirm(true)}
        disabled={closeAll.isPending}
      >
        {closeAll.isPending ? (
          <>
            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
            CLOSING...
          </>
        ) : (
          <>
            <AlertCircle className="w-5 h-5 mr-2" />
            PANIC CLOSE ALL
          </>
        )}
      </Button>

      <AlertDialog open={showConfirm} onOpenChange={setShowConfirm}>
        <AlertDialogContent className="bg-[#1A1F2E] border-gray-800">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">
              ⚠️ Close All Positions?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-gray-400">
              This will immediately close ALL open positions at market price.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-gray-800 text-white hover:bg-gray-700">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              className="bg-[#EF5350] hover:bg-[#D32F2F] text-white"
              onClick={handlePanic}
            >
              Yes, Close All
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
