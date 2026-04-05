/**
 * InstanceDeleteButton - Delete OSINT Instance with Confirmation
 *
 * Button to delete an OSINT instance with confirmation dialog
 */
import { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Trash2, Loader2 } from 'lucide-react';
import { useDeleteOsintInstance } from '../api';

interface InstanceDeleteButtonProps {
  instanceId: string;
  instanceName: string;
  size?: 'sm' | 'md' | 'lg';
  onDeleted?: () => void;
}

export function InstanceDeleteButton({
  instanceId,
  instanceName,
  size = 'md',
  onDeleted,
}: InstanceDeleteButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const deleteInstance = useDeleteOsintInstance();

  const handleDelete = async () => {
    try {
      await deleteInstance.mutateAsync(instanceId);
      setIsOpen(false);
      onDeleted?.();
    } catch (error) {
      // Error is handled by mutation
    }
  };

  const sizeClasses = {
    sm: 'p-1',
    md: 'p-2',
    lg: 'px-3 py-2',
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <AlertDialogTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          className={`rounded-md text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors ${sizeClasses[size]}`}
          title={`Delete ${instanceName}`}
        >
          <Trash2 className={iconSizes[size]} />
        </button>
      </AlertDialogTrigger>
      <AlertDialogContent onClick={(e) => e.stopPropagation()}>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Instance</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete <strong>{instanceName}</strong>? This action cannot be
            undone. All execution history and alerts associated with this instance will be
            permanently deleted.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteInstance.isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={deleteInstance.isPending}
            className="bg-red-500 hover:bg-red-600"
          >
            {deleteInstance.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default InstanceDeleteButton;
