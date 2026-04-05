import { useState } from 'react';
import { Check, X, Zap } from 'lucide-react';
import { useUpdateFeed } from '../api';

interface AnalyticsSettingsProps {
  feedId: string;
  currentSettings: {
    enable_analysis_v2: boolean;
  };
}

export function AnalyticsSettings({ feedId, currentSettings }: AnalyticsSettingsProps) {
  const { mutate: updateFeed, isPending } = useUpdateFeed();
  const [isEnabled, setIsEnabled] = useState(currentSettings.enable_analysis_v2);

  const handleToggle = () => {
    const newValue = !isEnabled;
    setIsEnabled(newValue);

    updateFeed(
      { feedId, updates: { enable_analysis_v2: newValue } },
      {
        onError: () => {
          // Revert on error
          setIsEnabled(!newValue);
        },
      }
    );
  };

  return (
    <div className="space-y-4 pt-4">
      <div className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/30">
        <div className="flex items-start gap-3 flex-1">
          <div className="flex-shrink-0 mt-1">
            <Zap className={`h-5 w-5 ${isEnabled ? 'text-primary' : 'text-muted-foreground'}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-sm font-semibold">Content Analysis V2</h3>
              {isEnabled ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  <Check className="h-3 w-3" />
                  Enabled
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                  <X className="h-3 w-3" />
                  Disabled
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Enables comprehensive AI-powered content analysis for new articles. The analysis pipeline automatically extracts entities, relationships,
              sentiment, categories, and generates summaries.
            </p>
          </div>
        </div>
        <div className="flex-shrink-0 ml-4">
          <button
            onClick={handleToggle}
            disabled={isPending}
            className={`
              relative inline-flex h-6 w-11 items-center rounded-full transition-colors
              ${isEnabled ? 'bg-primary' : 'bg-gray-200 dark:bg-gray-700'}
              ${isPending ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
            aria-label="Toggle content analysis"
          >
            <span
              className={`
                inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                ${isEnabled ? 'translate-x-6' : 'translate-x-1'}
              `}
            />
          </button>
        </div>
      </div>

      {isEnabled && (
        <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800">
          <p className="text-xs text-blue-900 dark:text-blue-100">
            <strong>Note:</strong> New articles from this feed will be automatically analyzed.
            Existing articles are not retroactively analyzed unless manually triggered.
          </p>
        </div>
      )}
    </div>
  );
}
