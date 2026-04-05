import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Edit, Save, XCircle, RefreshCw } from 'lucide-react';
import { useUpdateFeed } from '../api';
import { feedApi } from '@/api/axios';
import { useQueryClient } from '@tanstack/react-query';

interface ScrapingSettingsProps {
  feedId: string;
  currentSettings: {
    scrape_method: string;
    scrape_failure_threshold: number;
    scrape_full_content: boolean;
  };
}

interface FormValues {
  scrape_method: 'newspaper4k' | 'playwright';
  scrape_failure_threshold: number;
  scrape_full_content: boolean;
}

export function ScrapingSettings({ feedId, currentSettings }: ScrapingSettingsProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const { mutate: updateFeed, isPending } = useUpdateFeed();
  const queryClient = useQueryClient();

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      scrape_method: (currentSettings.scrape_method || 'newspaper4k') as 'newspaper4k' | 'playwright',
      scrape_failure_threshold: currentSettings.scrape_failure_threshold || 5,
      scrape_full_content: currentSettings.scrape_full_content,
    },
  });

  const formValues = watch();

  const onSubmit = (data: FormValues) => {
    updateFeed(
      { feedId, updates: data },
      {
        onSuccess: () => {
          setIsEditing(false);
        },
      }
    );
  };

  const onCancel = () => {
    reset({
      scrape_method: (currentSettings.scrape_method || 'newspaper4k') as 'newspaper4k' | 'playwright',
      scrape_failure_threshold: currentSettings.scrape_failure_threshold || 5,
      scrape_full_content: currentSettings.scrape_full_content,
    });
    setIsEditing(false);
  };

  const handleResetFailures = async () => {
    if (!confirm('Reset scraping failures? This will re-enable scraping if it was auto-disabled.')) {
      return;
    }

    setIsResetting(true);
    try {
      await feedApi.post(`/feeds/${feedId}/scraping/reset`);
      // Refetch feed data to show updated state
      await queryClient.invalidateQueries({ queryKey: ['feeds', 'detail', feedId] });
    } catch (error) {
      alert('Failed to reset scraping failures. Please try again.');
    } finally {
      setIsResetting(false);
    }
  };

  if (!isEditing) {
    // Read-only view
    return (
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-muted-foreground">
            Configure scraping method, failure threshold, and enable/disable full content scraping
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={handleResetFailures}
              disabled={isResetting}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-orange-500 text-white rounded-md hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Reset failure counter and re-enable scraping"
            >
              <RefreshCw className={`h-4 w-4 ${isResetting ? 'animate-spin' : ''}`} />
              {isResetting ? 'Resetting...' : 'Reset Failures'}
            </button>
            <button
              onClick={() => setIsEditing(true)}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              <Edit className="h-4 w-4" />
              Edit
            </button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3 rounded-lg border border-border bg-muted/30">
            <p className="text-xs font-medium text-muted-foreground mb-1">Scrape Method</p>
            <p className="text-sm font-semibold capitalize">{currentSettings.scrape_method || 'newspaper4k'}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {currentSettings.scrape_method === 'playwright'
                ? 'Full browser (JavaScript support)'
                : 'Fast extraction with AI (handles cookie banners)'}
            </p>
          </div>
          <div className="p-3 rounded-lg border border-border bg-muted/30">
            <p className="text-xs font-medium text-muted-foreground mb-1">Failure Threshold</p>
            <p className="text-sm font-semibold">{currentSettings.scrape_failure_threshold || 5} failures</p>
            <p className="text-xs text-muted-foreground mt-1">
              Auto-disable scraping after reaching this limit
            </p>
          </div>
          <div className="p-3 rounded-lg border border-border bg-muted/30">
            <p className="text-xs font-medium text-muted-foreground mb-1">Full Content Scraping</p>
            <p className="text-sm font-semibold">
              {currentSettings.scrape_full_content ? 'Enabled' : 'Disabled'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {currentSettings.scrape_full_content
                ? 'Extracting full article content'
                : 'Using RSS description only'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Edit mode
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 pt-4">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-muted-foreground">
          Configure scraping method, failure threshold, and enable/disable full content scraping
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Scrape Method */}
        <div className="p-4 rounded-lg border border-border bg-card">
          <label className="block text-sm font-medium mb-2">
            Scraping Method
          </label>
          <select
            {...register('scrape_method')}
            disabled={isPending}
            className="w-full px-3 py-2 rounded-md border border-input bg-background text-foreground disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="newspaper4k">Newspaper4k (Recommended)</option>
            <option value="playwright">Playwright (Full Browser)</option>
          </select>
          <p className="text-xs text-muted-foreground mt-2">
            {formValues.scrape_method === 'playwright'
              ? 'Uses full browser with JavaScript support. Slower but handles complex sites.'
              : 'Fast AI-powered extraction. Automatically handles cookie banners and most sites.'}
          </p>
        </div>

        {/* Failure Threshold */}
        <div className="p-4 rounded-lg border border-border bg-card">
          <label className="block text-sm font-medium mb-2">
            Failure Threshold (1-20)
          </label>
          <input
            type="number"
            {...register('scrape_failure_threshold', {
              required: 'Threshold is required',
              min: { value: 1, message: 'Minimum is 1' },
              max: { value: 20, message: 'Maximum is 20' },
              valueAsNumber: true,
            })}
            disabled={isPending}
            min={1}
            max={20}
            className="w-full px-3 py-2 rounded-md border border-input bg-background text-foreground disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {errors.scrape_failure_threshold && (
            <p className="text-xs text-red-500 mt-1">{errors.scrape_failure_threshold.message}</p>
          )}
          <p className="text-xs text-muted-foreground mt-2">
            Scraping will be auto-disabled after this many consecutive failures
          </p>
        </div>

        {/* Full Content Scraping Toggle */}
        <div className="p-4 rounded-lg border border-border bg-card col-span-1 md:col-span-2">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              {...register('scrape_full_content')}
              disabled={isPending}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary disabled:opacity-50"
            />
            <div className="flex-1">
              <p className="text-sm font-medium">Enable Full Content Scraping</p>
              <p className="text-xs text-muted-foreground mt-1">
                Extract full article content from source URLs. If disabled, only RSS feed descriptions are used.
              </p>
            </div>
          </label>
        </div>
      </div>
      <div className="flex items-center gap-3 pt-4 border-t border-border">
        <button
          type="submit"
          disabled={isPending}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Save className="h-4 w-4" />
          {isPending ? 'Saving...' : 'Save Changes'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isPending}
          className="inline-flex items-center gap-2 px-4 py-2 bg-muted text-foreground rounded-md hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <XCircle className="h-4 w-4" />
          Cancel
        </button>
      </div>
    </form>
  );
}
