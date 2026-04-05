/**
 * InstanceExecuteButton - Execute OSINT Instance Button
 *
 * Button to trigger manual execution of an OSINT instance
 */
import { useState } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { useExecuteOsint } from '../api';

interface InstanceExecuteButtonProps {
  instanceId: string;
  instanceName: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  onExecutionStarted?: (executionId: string) => void;
}

export function InstanceExecuteButton({
  instanceId,
  instanceName,
  disabled = false,
  size = 'md',
  onExecutionStarted,
}: InstanceExecuteButtonProps) {
  const executeOsint = useExecuteOsint();

  const handleExecute = async (e: React.MouseEvent) => {
    e.stopPropagation();

    try {
      const result = await executeOsint.mutateAsync({ instance_id: instanceId });
      onExecutionStarted?.(result.execution.id);
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

  return (
    <button
      onClick={handleExecute}
      disabled={disabled || executeOsint.isPending}
      className={`inline-flex items-center gap-1 rounded-md bg-green-500 font-medium text-white hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${sizeClasses[size]}`}
      title={disabled ? 'Instance is disabled' : `Execute ${instanceName}`}
    >
      {executeOsint.isPending ? (
        <Loader2 className={`${iconSizes[size]} animate-spin`} />
      ) : (
        <Play className={iconSizes[size]} />
      )}
      {size !== 'sm' && (executeOsint.isPending ? 'Running...' : 'Run')}
    </button>
  );
}

export default InstanceExecuteButton;
