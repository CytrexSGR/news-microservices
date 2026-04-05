/**
 * StrategyHeader Component
 *
 * Displays the strategy name, version, description, and navigation
 * Supports inline editing of name and description when edit mode is active.
 */

import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Eye } from 'lucide-react';
import type { StrategyDefinition } from '../types';
import { EditableField } from './shared/EditableField';
import { useStrategyEditContext } from '../context';

interface StrategyHeaderProps {
  definition: StrategyDefinition;
  backPath?: string;
}

// ============================================================================
// Sub-components for Editable Metadata
// ============================================================================

interface EditableNameProps {
  name: string;
}

/**
 * Editable strategy name component
 */
function EditableName({ name }: EditableNameProps) {
  try {
    const { isEditMode, updateDefinition, isPending } = useStrategyEditContext();

    return (
      <EditableField
        value={name}
        type="text"
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={(value) => updateDefinition({ name: value as string })}
        displayClassName="text-3xl font-bold"
        inputClassName="text-2xl font-bold h-10"
        label="Strategy Name"
      />
    );
  } catch {
    // Fallback when not wrapped in StrategyEditProvider
    return <h1 className="text-3xl font-bold">{name}</h1>;
  }
}

interface EditableDescriptionProps {
  description: string;
}

/**
 * Editable strategy description component
 */
function EditableDescription({ description }: EditableDescriptionProps) {
  try {
    const { isEditMode, updateDefinition, isPending } = useStrategyEditContext();

    return (
      <EditableField
        value={description}
        type="text"
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={(value) => updateDefinition({ description: value as string })}
        displayClassName="text-muted-foreground"
        inputClassName="w-full max-w-lg"
        label="Description"
        placeholder="Strategy description..."
      />
    );
  } catch {
    // Fallback when not wrapped in StrategyEditProvider
    return <p className="text-muted-foreground mt-1">{description}</p>;
  }
}

interface EditableVersionProps {
  version: string;
}

/**
 * Editable strategy version component
 */
function EditableVersion({ version }: EditableVersionProps) {
  try {
    const { isEditMode, updateDefinition, isPending } = useStrategyEditContext();

    return (
      <EditableField
        value={version}
        type="text"
        canEdit={isEditMode && !isPending}
        showEditIndicator={isEditMode}
        onSave={(value) => updateDefinition({ version: value as string })}
        inputClassName="w-24"
        label="Version"
      />
    );
  } catch {
    // Fallback when not wrapped in StrategyEditProvider
    return <Badge variant="outline">{version}</Badge>;
  }
}

// ============================================================================
// Main Component
// ============================================================================

export function StrategyHeader({ definition, backPath = '/trading/debug' }: StrategyHeaderProps) {
  const navigate = useNavigate();

  return (
    <div className="flex items-center gap-4">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => navigate(backPath)}
      >
        <ArrowLeft className="h-5 w-5" />
      </Button>
      <div>
        <div className="flex items-center gap-2">
          <Eye className="h-8 w-8 text-primary" />
          <EditableName name={definition.name} />
          <EditableVersion version={definition.version} />
        </div>
        <div className="mt-1">
          <EditableDescription description={definition.description} />
        </div>
      </div>
    </div>
  );
}
