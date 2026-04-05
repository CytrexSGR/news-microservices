import type { UseFormReturn } from 'react-hook-form';
import { Input } from '@/components/ui/Input';
import type { CreateFeedFormData } from '../types/createFeed';
import { FEED_CATEGORIES } from '../types/createFeed';

interface FeedBasicInfoStepProps {
  form: UseFormReturn<CreateFeedFormData, any, any>;
  isAssessmentDataAvailable?: boolean;
}

export function FeedBasicInfoStep({ form, isAssessmentDataAvailable }: FeedBasicInfoStepProps) {
  const { register, formState: { errors } } = form;

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Grundlegende Informationen</h3>
        <p className="text-sm text-muted-foreground mb-6">
          Geben Sie die URL und den Namen des RSS/Atom Feeds ein. Im nächsten Schritt können Sie ein
          Source Assessment durchführen lassen, welches automatisch eine detaillierte Beschreibung,
          Kategorien und Bewertungsinformationen generiert.
        </p>
      </div>

      {/* URL Field */}
      <div>
        <label htmlFor="url" className="block text-sm font-medium mb-2">
          Feed URL *
        </label>
        <Input
          id="url"
          type="url"
          placeholder="https://example.com/rss"
          {...register('url')}
          className="w-full"
        />
        {errors.url?.message && (
          <p className="text-xs text-red-500 mt-1">{errors.url.message}</p>
        )}
        <p className="text-xs text-muted-foreground mt-1">
          Die vollständige URL zum RSS oder Atom Feed
        </p>
      </div>

      {/* Name Field */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-2">
          Feed Name *
          {isAssessmentDataAvailable && (
            <span className="ml-2 text-xs text-blue-500">(Vorbefüllt durch Assessment)</span>
          )}
        </label>
        <Input
          id="name"
          type="text"
          placeholder="z.B. TechCrunch News"
          {...register('name')}
          className="w-full"
        />
        {errors.name?.message && (
          <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>
        )}
      </div>

      {/* Fetch Interval */}
      <div>
        <label htmlFor="fetch_interval" className="block text-sm font-medium mb-2">
          Fetch-Intervall (Minuten)
        </label>
        <div className="flex items-center gap-4">
          <input
            id="fetch_interval"
            type="range"
            min="5"
            max="1440"
            step="5"
            {...register('fetch_interval', { valueAsNumber: true })}
            className="flex-1"
          />
          <span className="text-sm font-medium min-w-[80px]">
            {form.watch('fetch_interval')} min
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Wie oft soll der Feed abgerufen werden? (5-1440 Minuten)
        </p>
        {errors.fetch_interval && (
          <p className="text-xs text-destructive mt-1">{errors.fetch_interval.message}</p>
        )}
      </div>

      {/* Category - Only show if assessment has run */}
      {isAssessmentDataAvailable && (
        <div>
          <label htmlFor="category" className="block text-sm font-medium mb-2">
            Kategorie
            <span className="ml-2 text-xs text-blue-500">(✓ Automatisch bestimmt)</span>
          </label>
          <select
            id="category"
            {...register('category')}
            className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">-- Bitte wählen --</option>
            {FEED_CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground mt-1">
            Die Kategorie wurde automatisch vom Assessment bestimmt, kann aber bei Bedarf geändert werden.
          </p>
          {errors.category && (
            <p className="text-xs text-destructive mt-1">{errors.category.message}</p>
          )}
        </div>
      )}
      {!isAssessmentDataAvailable && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            💡 Die Kategorie wird automatisch im nächsten Schritt durch das Assessment bestimmt
          </p>
        </div>
      )}
    </div>
  );
}
