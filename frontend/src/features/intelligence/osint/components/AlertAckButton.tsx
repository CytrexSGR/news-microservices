/**
 * AlertAckButton - Acknowledge OSINT Alert Button
 *
 * Button to acknowledge an alert with optional confirmation
 */
import { useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import { useAcknowledgeAlert } from '../api';

interface AlertAckButtonProps {
  alertId: string;
  alertTitle: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  onAcknowledged?: () => void;
}

export function AlertAckButton({
  alertId,
  alertTitle,
  size = 'md',
  showLabel = true,
  onAcknowledged,
}: AlertAckButtonProps) {
  const [comment, setComment] = useState('');
  const [showInput, setShowInput] = useState(false);
  const acknowledgeAlert = useAcknowledgeAlert();

  const handleAcknowledge = async (e: React.MouseEvent) => {
    e.stopPropagation();

    try {
      await acknowledgeAlert.mutateAsync({
        alert_id: alertId,
        comment: comment || undefined,
      });
      setShowInput(false);
      setComment('');
      onAcknowledged?.();
    } catch (error) {
      // Error is handled by mutation
    }
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  if (showInput) {
    return (
      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
        <input
          type="text"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Optional comment..."
          className="rounded-md border bg-background px-2 py-1 text-sm w-40"
          autoFocus
        />
        <button
          onClick={handleAcknowledge}
          disabled={acknowledgeAlert.isPending}
          className="rounded-md bg-green-500 px-2 py-1 text-xs text-white hover:bg-green-600 disabled:opacity-50"
        >
          {acknowledgeAlert.isPending ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Check className="h-3 w-3" />
          )}
        </button>
        <button
          onClick={() => setShowInput(false)}
          className="rounded-md border px-2 py-1 text-xs hover:bg-muted"
        >
          Cancel
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        // For quick ack, directly acknowledge without comment
        // Or show input for comment
        setShowInput(true);
      }}
      disabled={acknowledgeAlert.isPending}
      className={`inline-flex items-center gap-1 rounded-md bg-green-500 font-medium text-white hover:bg-green-600 disabled:opacity-50 transition-colors ${sizeClasses[size]}`}
      title={`Acknowledge: ${alertTitle}`}
    >
      {acknowledgeAlert.isPending ? (
        <Loader2 className={`${iconSizes[size]} animate-spin`} />
      ) : (
        <Check className={iconSizes[size]} />
      )}
      {showLabel && size !== 'sm' && 'Acknowledge'}
    </button>
  );
}

export default AlertAckButton;
