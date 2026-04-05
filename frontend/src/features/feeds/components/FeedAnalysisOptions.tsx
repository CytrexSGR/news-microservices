import type { UseFormReturn } from 'react-hook-form';
import { ToggleLeft, ToggleRight, Sparkles, TrendingUp, Globe, Shield, FileText, Users, Tags, AlertTriangle, Swords } from 'lucide-react';
import type { CreateFeedFormData } from '../types/createFeed';

interface FeedAnalysisOptionsProps {
  form: UseFormReturn<CreateFeedFormData, any, any>;
}

export function FeedAnalysisOptions({ form }: FeedAnalysisOptionsProps) {
  const { setValue, watch } = form;

  const allOptions = [
    'enable_categorization',
    'enable_finance_sentiment',
    'enable_geopolitical_sentiment',
    'enable_bias',
    'enable_conflict',
    'enable_osint_analysis',
    'enable_summary',
    'enable_entity_extraction',
    'enable_topic_classification',
  ] as const;

  // Watch all analysis options (unused but kept for future validation)
  // const watchedOptions = watch(allOptions as any);

  const handleEnableAll = () => {
    allOptions.forEach((option) => setValue(option, true));
  };

  const handleDisableAll = () => {
    allOptions.forEach((option) => setValue(option, false));
  };

  const AnalysisToggle = ({
    name,
    label,
    description,
    icon: Icon
  }: {
    name: keyof CreateFeedFormData;
    label: string;
    description: string;
    icon: any;
  }) => {
    const isEnabled = watch(name) as boolean;

    return (
      <div className="flex items-start gap-4 p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors">
        <div className="flex-shrink-0 mt-1">
          <Icon className={`h-5 w-5 ${isEnabled ? 'text-primary' : 'text-muted-foreground'}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-4 mb-1">
            <label htmlFor={name} className="text-sm font-medium cursor-pointer">
              {label}
            </label>
            <button
              type="button"
              id={name}
              onClick={() => setValue(name, !isEnabled)}
              className="flex-shrink-0"
            >
              {isEnabled ? (
                <ToggleRight className="h-6 w-6 text-primary" />
              ) : (
                <ToggleLeft className="h-6 w-6 text-muted-foreground" />
              )}
            </button>
          </div>
          <p className="text-xs text-muted-foreground">
            {description}
          </p>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Auto-Analysis Optionen</h3>
        <p className="text-sm text-muted-foreground">
          Wählen Sie aus, welche Analysen automatisch bei neuen Artikeln durchgeführt werden sollen.
          Alle Optionen sind standardmäßig aktiviert.
        </p>
      </div>

      {/* Bulk Action Buttons */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={handleEnableAll}
          className="flex-1 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
        >
          Alle aktivieren
        </button>
        <button
          type="button"
          onClick={handleDisableAll}
          className="flex-1 px-4 py-2 text-sm font-medium bg-muted text-foreground rounded-md hover:bg-muted/80 transition-colors"
        >
          Alle deaktivieren
        </button>
      </div>

      {/* Analysis Options Groups */}
      <div className="space-y-4">
        {/* Content Analysis */}
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Content-Analyse
          </h4>
          <div className="space-y-2">
            <AnalysisToggle
              name="enable_categorization"
              label="Artikel-Kategorisierung"
              description="Automatische Kategorisierung in 6 vordefinierte Kategorien"
              icon={Tags}
            />
            <AnalysisToggle
              name="enable_topic_classification"
              label="Topic-Klassifikation & Keywords"
              description="Erkennung von Themen, Hierarchien und relevanten Schlüsselwörtern"
              icon={Sparkles}
            />
            <AnalysisToggle
              name="enable_entity_extraction"
              label="Entity-Extraktion"
              description="Erkennung von Personen, Organisationen und Orten im Text"
              icon={Users}
            />
          </div>
        </div>

        {/* Sentiment Analysis */}
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Sentiment-Analyse
          </h4>
          <div className="space-y-2">
            <AnalysisToggle
              name="enable_finance_sentiment"
              label="Finanz-Sentiment-Analyse"
              description="Markt-Sentiment, Volatilität und wirtschaftliche Auswirkungen"
              icon={TrendingUp}
            />
            <AnalysisToggle
              name="enable_geopolitical_sentiment"
              label="Geopolitische Sentiment-Analyse"
              description="Stabilitäts-Scores, Eskalationspotenzial und diplomatische Auswirkungen"
              icon={Globe}
            />
            <AnalysisToggle
              name="enable_bias"
              label="Bias-Detection"
              description="Erkennung von Bias, Voreingenommenheit und einseitiger Berichterstattung"
              icon={AlertTriangle}
            />
            <AnalysisToggle
              name="enable_conflict"
              label="Konflikt-Event-Analyse"
              description="Analyse von Konflikt-Events, Gewalt und sicherheitsrelevanten Vorfällen"
              icon={Swords}
            />
          </div>
        </div>

        {/* Intelligence & Summarization */}
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-3 uppercase tracking-wide">
            Intelligence & Zusammenfassung
          </h4>
          <div className="space-y-2">
            <AnalysisToggle
              name="enable_osint_analysis"
              label="OSINT Event Analysis"
              description="Open Source Intelligence Analyse für sicherheitsrelevante Events"
              icon={Shield}
            />
            <AnalysisToggle
              name="enable_summary"
              label="Zusammenfassung & Key Facts"
              description="Automatische Zusammenfassung mit wichtigsten Punkten"
              icon={FileText}
            />
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-sm text-blue-900 dark:text-blue-100">
          <strong>Hinweis:</strong> Aktivierte Analysen werden bei jedem neuen Artikel automatisch durchgeführt.
          Sie können diese Einstellungen später jederzeit ändern.
        </p>
      </div>
    </div>
  );
}
