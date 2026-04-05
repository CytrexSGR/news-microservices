/**
 * ResearchExportButton Component
 *
 * Dropdown button to export research results in different formats:
 * - PDF
 * - Markdown
 * - JSON
 */

import { useState, useRef, useEffect } from 'react';
import {
  Download,
  FileText,
  FileJson,
  File,
  Loader2,
  ChevronDown,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useExportResearch } from '../api';
import type { ExportFormat } from '../types';

interface ResearchExportButtonProps {
  taskId: number;
  disabled?: boolean;
  includeSources?: boolean;
  includeMetadata?: boolean;
}

const EXPORT_OPTIONS: {
  format: ExportFormat;
  label: string;
  icon: React.ReactNode;
  description: string;
}[] = [
  {
    format: 'pdf',
    label: 'PDF',
    icon: <File className="h-4 w-4" />,
    description: 'Portable Document Format',
  },
  {
    format: 'markdown',
    label: 'Markdown',
    icon: <FileText className="h-4 w-4" />,
    description: 'Markdown text file',
  },
  {
    format: 'json',
    label: 'JSON',
    icon: <FileJson className="h-4 w-4" />,
    description: 'Raw JSON data',
  },
];

export function ResearchExportButton({
  taskId,
  disabled = false,
  includeSources = true,
  includeMetadata = true,
}: ResearchExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const exportMutation = useExportResearch();

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleExport = async (format: ExportFormat) => {
    setIsOpen(false);
    await exportMutation.mutateAsync({
      taskId,
      format,
      options: {
        include_sources: includeSources,
        include_metadata: includeMetadata,
      },
    });
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || exportMutation.isPending}
        className="gap-2"
      >
        {exportMutation.isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Exporting...
          </>
        ) : (
          <>
            <Download className="h-4 w-4" />
            Export
            <ChevronDown className="h-3 w-3" />
          </>
        )}
      </Button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-popover border border-border rounded-lg shadow-lg z-50">
          <div className="p-1">
            {EXPORT_OPTIONS.map((option) => (
              <button
                key={option.format}
                onClick={() => handleExport(option.format)}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-foreground hover:bg-accent rounded-md transition-colors"
              >
                <span className="text-muted-foreground">{option.icon}</span>
                <div className="text-left">
                  <p className="font-medium">{option.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {option.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
