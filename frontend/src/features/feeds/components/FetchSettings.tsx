import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Edit, Save, XCircle, Clock } from 'lucide-react';
import { useUpdateFeed } from '../api';

interface FetchSettingsProps {
  feedId: string;
  currentSettings: {
    fetch_interval: number;
  };
}

interface FormValues {
  fetch_interval: number;
}

export function FetchSettings({ feedId, currentSettings }: FetchSettingsProps) {
  const [isEditing, setIsEditing] = useState(false);
  const { mutate: updateFeed, isPending } = useUpdateFeed();

  const { register, handleSubmit, reset, watch, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      fetch_interval: currentSettings.fetch_interval,
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
      fetch_interval: currentSettings.fetch_interval,
    });
    setIsEditing(false);
  };

  // Helper to display interval in human-readable format
  const formatInterval = (minutes: number) => {
    if (minutes < 60) {
      return `${minutes} minutes`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (remainingMinutes === 0) {
      return `${hours} ${hours === 1 ? 'hour' : 'hours'}`;
    }
    return `${hours}h ${remainingMinutes}m`;
  };

  // Helper to suggest common intervals
  const getIntervalRecommendation = (minutes: number) => {
    if (minutes <= 15) return 'Very frequent - High server load';
    if (minutes <= 30) return 'Frequent - Good for breaking news';
    if (minutes <= 60) return 'Standard - Balanced performance';
    if (minutes <= 180) return 'Moderate - Low priority feeds';
    return 'Infrequent - Archive/slow feeds';
  };

  if (!isEditing) {
    // Read-only view
    return (
      <div className="space-y-4 pt-4">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-muted-foreground">
            Configure how often this feed should be checked for new articles
          </p>
          <button
            onClick={() => setIsEditing(true)}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Edit className="h-4 w-4" />
            Edit
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3 rounded-lg border border-border bg-muted/30">
            <p className="text-xs font-medium text-muted-foreground mb-1">Fetch Interval</p>
            <p className="text-sm font-semibold flex items-center gap-2">
              <Clock className="h-4 w-4" />
              {formatInterval(currentSettings.fetch_interval)}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {getIntervalRecommendation(currentSettings.fetch_interval)}
            </p>
          </div>
          <div className="p-3 rounded-lg border border-border bg-muted/30">
            <p className="text-xs font-medium text-muted-foreground mb-1">Fetches per Day</p>
            <p className="text-sm font-semibold">
              ~{Math.round((24 * 60) / currentSettings.fetch_interval)} times
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Estimated daily fetch count
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
          Configure how often this feed should be checked for new articles
        </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Fetch Interval Input */}
        <div className="p-4 rounded-lg border border-border bg-card">
          <label className="block text-sm font-medium mb-2">
            Fetch Interval (5-1440 minutes)
          </label>
          <input
            type="number"
            {...register('fetch_interval', {
              required: 'Fetch interval is required',
              min: { value: 5, message: 'Minimum is 5 minutes' },
              max: { value: 1440, message: 'Maximum is 1440 minutes (24 hours)' },
              valueAsNumber: true,
            })}
            disabled={isPending}
            min={5}
            max={1440}
            step={5}
            className="w-full px-3 py-2 rounded-md border border-input bg-background text-foreground disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {errors.fetch_interval && (
            <p className="text-xs text-red-500 mt-1">{errors.fetch_interval.message}</p>
          )}
          <p className="text-xs text-muted-foreground mt-2">
            {formatInterval(formValues.fetch_interval || 60)}
          </p>
        </div>

        {/* Live Preview */}
        <div className="p-4 rounded-lg border border-border bg-card">
          <p className="text-sm font-medium mb-2">Preview</p>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Fetches per day:</span>
              <span className="font-semibold">
                ~{Math.round((24 * 60) / (formValues.fetch_interval || 60))} times
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Recommendation:</span>
              <span className="font-medium text-primary">
                {getIntervalRecommendation(formValues.fetch_interval || 60)}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Presets */}
        <div className="p-4 rounded-lg border border-border bg-card col-span-1 md:col-span-2">
          <p className="text-sm font-medium mb-3">Quick Presets</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => reset({ fetch_interval: 15 })}
              disabled={isPending}
              className="px-3 py-1.5 text-xs rounded-md border border-border hover:bg-muted disabled:opacity-50 transition-colors"
            >
              15 min (Breaking News)
            </button>
            <button
              type="button"
              onClick={() => reset({ fetch_interval: 30 })}
              disabled={isPending}
              className="px-3 py-1.5 text-xs rounded-md border border-border hover:bg-muted disabled:opacity-50 transition-colors"
            >
              30 min (Active News)
            </button>
            <button
              type="button"
              onClick={() => reset({ fetch_interval: 60 })}
              disabled={isPending}
              className="px-3 py-1.5 text-xs rounded-md border border-border hover:bg-muted disabled:opacity-50 transition-colors"
            >
              1 hour (Standard)
            </button>
            <button
              type="button"
              onClick={() => reset({ fetch_interval: 120 })}
              disabled={isPending}
              className="px-3 py-1.5 text-xs rounded-md border border-border hover:bg-muted disabled:opacity-50 transition-colors"
            >
              2 hours (Moderate)
            </button>
            <button
              type="button"
              onClick={() => reset({ fetch_interval: 360 })}
              disabled={isPending}
              className="px-3 py-1.5 text-xs rounded-md border border-border hover:bg-muted disabled:opacity-50 transition-colors"
            >
              6 hours (Low Priority)
            </button>
            <button
              type="button"
              onClick={() => reset({ fetch_interval: 720 })}
              disabled={isPending}
              className="px-3 py-1.5 text-xs rounded-md border border-border hover:bg-muted disabled:opacity-50 transition-colors"
            >
              12 hours (Archive)
            </button>
          </div>
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
