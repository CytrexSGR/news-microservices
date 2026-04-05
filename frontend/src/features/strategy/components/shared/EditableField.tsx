/**
 * EditableField Component
 *
 * Generic inline edit field supporting text, number, and select inputs.
 * Shows view mode by default, switches to edit mode on click when enabled.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { Input } from '@/components/ui/Input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/Button';
import { Check, X, Pencil } from 'lucide-react';
import { cn } from '@/lib/utils';

// ============================================================================
// Types
// ============================================================================

export type EditableFieldType = 'text' | 'number' | 'select';

export interface SelectOption {
  value: string;
  label: string;
}

export interface EditableFieldProps {
  /** Current value */
  value: string | number;
  /** Input type */
  type?: EditableFieldType;
  /** Options for select type */
  options?: SelectOption[];
  /** External edit mode control */
  isEditing?: boolean;
  /** Whether editing is allowed */
  canEdit?: boolean;
  /** Whether global edit mode is active (shows visual indicator) */
  showEditIndicator?: boolean;
  /** Callback when value is saved */
  onSave: (value: string | number) => void | Promise<void>;
  /** Callback when edit is cancelled */
  onCancel?: () => void;
  /** Container class */
  className?: string;
  /** Input class */
  inputClassName?: string;
  /** Display class */
  displayClassName?: string;
  /** Placeholder text */
  placeholder?: string;
  /** Min value for number type */
  min?: number;
  /** Max value for number type */
  max?: number;
  /** Step for number type */
  step?: number;
  /** Suffix to display after value */
  suffix?: string;
  /** Prefix to display before value */
  prefix?: string;
  /** Custom display formatter */
  formatDisplay?: (value: string | number) => string;
  /** Label to show what field this is */
  label?: string;
}

// ============================================================================
// Component
// ============================================================================

export function EditableField({
  value,
  type = 'text',
  options = [],
  isEditing: externalIsEditing,
  canEdit = true,
  showEditIndicator = false,
  onSave,
  onCancel,
  className,
  inputClassName,
  displayClassName,
  placeholder,
  min,
  max,
  step,
  suffix,
  prefix,
  formatDisplay,
  label,
}: EditableFieldProps) {
  const [internalIsEditing, setInternalIsEditing] = useState(false);
  const [editValue, setEditValue] = useState<string | number>(value);
  const [isSaving, setIsSaving] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const isEditing = externalIsEditing ?? internalIsEditing;

  // Sync edit value with prop value
  useEffect(() => {
    setEditValue(value);
  }, [value]);

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      const finalValue = type === 'number' ? Number(editValue) : editValue;
      await onSave(finalValue);
      setInternalIsEditing(false);
    } catch (error) {
      console.error('Failed to save:', error);
    } finally {
      setIsSaving(false);
    }
  }, [editValue, type, onSave]);

  const handleCancel = useCallback(() => {
    setEditValue(value);
    setInternalIsEditing(false);
    onCancel?.();
  }, [value, onCancel]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleSave();
      } else if (e.key === 'Escape') {
        handleCancel();
      }
    },
    [handleSave, handleCancel]
  );

  const displayValue = formatDisplay
    ? formatDisplay(value)
    : `${prefix || ''}${value}${suffix || ''}`;

  // ============================================================================
  // View Mode
  // ============================================================================

  // Determine if we should show the editable indicator
  const showIndicator = canEdit && showEditIndicator;

  if (!isEditing) {
    return (
      <div
        className={cn(
          'group flex items-center gap-2 rounded transition-all',
          showIndicator && [
            'px-2 py-1 -mx-2 -my-1',
            'border border-dashed border-blue-400/50',
            'bg-blue-50/50 dark:bg-blue-950/20',
            'hover:border-blue-500 hover:bg-blue-100/50 dark:hover:bg-blue-900/30',
            'cursor-pointer',
          ],
          className
        )}
        onClick={showIndicator ? () => setInternalIsEditing(true) : undefined}
        title={showIndicator ? `Click to edit${label ? `: ${label}` : ''}` : undefined}
      >
        {label && showIndicator && (
          <span className="text-xs text-blue-600 dark:text-blue-400 font-medium mr-1">
            {label}:
          </span>
        )}
        <span className={cn('font-mono', displayClassName)}>
          {displayValue || (
            <span className="text-muted-foreground">{placeholder || '—'}</span>
          )}
        </span>
        {canEdit && (
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              'h-6 w-6 transition-opacity',
              showIndicator
                ? 'opacity-70 hover:opacity-100 text-blue-600 dark:text-blue-400'
                : 'opacity-0 group-hover:opacity-100'
            )}
            onClick={(e) => {
              e.stopPropagation();
              setInternalIsEditing(true);
            }}
          >
            <Pencil className="h-3 w-3" />
          </Button>
        )}
      </div>
    );
  }

  // ============================================================================
  // Select Mode
  // ============================================================================

  if (type === 'select') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <Select
          value={String(editValue)}
          onValueChange={(v) => {
            setEditValue(v);
            onSave(v);
            setInternalIsEditing(false);
          }}
        >
          <SelectTrigger className={cn('h-8', inputClassName)}>
            <SelectValue placeholder={placeholder} />
          </SelectTrigger>
          <SelectContent>
            {options.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleCancel}>
          <X className="h-3 w-3" />
        </Button>
      </div>
    );
  }

  // ============================================================================
  // Text/Number Mode
  // ============================================================================

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {prefix && <span className="text-muted-foreground text-sm">{prefix}</span>}
      <Input
        ref={inputRef}
        type={type}
        value={editValue}
        onChange={(e) =>
          setEditValue(type === 'number' ? e.target.value : e.target.value)
        }
        onKeyDown={handleKeyDown}
        className={cn('h-8 font-mono', inputClassName)}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        disabled={isSaving}
      />
      {suffix && <span className="text-muted-foreground text-sm">{suffix}</span>}
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6"
        onClick={handleSave}
        disabled={isSaving}
      >
        <Check className="h-3 w-3" />
      </Button>
      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleCancel}>
        <X className="h-3 w-3" />
      </Button>
    </div>
  );
}
