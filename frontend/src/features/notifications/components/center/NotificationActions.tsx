/**
 * NotificationActions Component
 *
 * Bulk action bar for selected notifications.
 */

import { CheckCheck, Archive, Trash2, X, CheckSquare } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface NotificationActionsProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: () => void;
  onAction: (action: 'read' | 'archive' | 'delete') => void;
  isLoading?: boolean;
  className?: string;
}

export function NotificationActions({
  selectedCount,
  totalCount,
  onSelectAll,
  onAction,
  isLoading = false,
  className,
}: NotificationActionsProps) {
  const allSelected = selectedCount === totalCount && totalCount > 0;

  return (
    <div
      className={cn(
        'flex items-center justify-between p-3 rounded-lg',
        'bg-primary/5 border border-primary/20',
        'animate-in slide-in-from-top-2 duration-200',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={onSelectAll}
          className="gap-2"
        >
          <CheckSquare className="h-4 w-4" />
          {allSelected ? 'Deselect all' : 'Select all'}
        </Button>
        <span className="text-sm text-muted-foreground">
          {selectedCount} selected
        </span>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onAction('read')}
          disabled={isLoading}
          className="gap-2"
        >
          <CheckCheck className="h-4 w-4" />
          <span className="hidden sm:inline">Mark as read</span>
        </Button>

        <Button
          variant="secondary"
          size="sm"
          onClick={() => onAction('archive')}
          disabled={isLoading}
          className="gap-2"
        >
          <Archive className="h-4 w-4" />
          <span className="hidden sm:inline">Archive</span>
        </Button>

        <Button
          variant="destructive"
          size="sm"
          onClick={() => onAction('delete')}
          disabled={isLoading}
          className="gap-2"
        >
          <Trash2 className="h-4 w-4" />
          <span className="hidden sm:inline">Delete</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onSelectAll}
          className="ml-2"
          title="Clear selection"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
