import type { UseFormReturn } from 'react-hook-form';
import { RefreshCw, Info, AlertTriangle, Star, Shield } from 'lucide-react';
import type { CreateFeedFormData, PreAssessmentResponse } from '../types/createFeed';

interface FeedAssessmentStepProps {
  form: UseFormReturn<CreateFeedFormData, any, any>;
  assessmentData?: PreAssessmentResponse['assessment'];
  onRunAssessment: () => void;
  isAssessing: boolean;
  assessmentError?: Error | null;
}

export function FeedAssessmentStep({
  form,
  assessmentData,
  onRunAssessment,
  isAssessing,
  assessmentError,
}: FeedAssessmentStepProps) {
  const url = form.watch('url');
  const canRunAssessment = url && url.startsWith('http');

  const getCredibilityBadge = (tier?: string) => {
    if (!tier) return null;
    const colors = {
      tier_1: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      tier_2: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      tier_3: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[tier as keyof typeof colors] || ''}`}>
        {tier.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const getPoliticalBiasColor = (bias?: string) => {
    if (!bias) return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    const biasLower = bias.toLowerCase();
    if (biasLower.includes('left')) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    if (biasLower.includes('right')) return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Source Assessment (Optional)</h3>
        <p className="text-sm text-muted-foreground">
          Führen Sie eine Bewertung der Quelle durch, um automatisch Informationen über
          Glaubwürdigkeit, politische Ausrichtung und redaktionelle Standards zu erhalten.
        </p>
      </div>

      {/* Run Assessment Button */}
      <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg border border-border">
        <button
          type="button"
          onClick={onRunAssessment}
          disabled={!canRunAssessment || isAssessing}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${isAssessing ? 'animate-spin' : ''}`} />
          {isAssessing ? 'Assessment läuft...' : 'Source Assessment durchführen'}
        </button>
        {!canRunAssessment && (
          <p className="text-sm text-muted-foreground">
            Bitte geben Sie zunächst eine gültige URL ein
          </p>
        )}
      </div>

      {/* Assessment Error */}
      {assessmentError && (
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
            <div>
              <p className="text-sm font-medium text-destructive">Assessment fehlgeschlagen</p>
              <p className="text-xs text-muted-foreground mt-1">
                {assessmentError.message}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Sie können trotzdem fortfahren und den Feed manuell erstellen.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Assessment Results */}
      {assessmentData && (
        <div className="space-y-6">
          {/* Summary */}
          {assessmentData.assessment_summary && (
            <div className="bg-blue-50 dark:bg-blue-950/30 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-start gap-2">
                <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                    Assessment Zusammenfassung
                  </p>
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    {assessmentData.assessment_summary}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Credibility Tier */}
            {assessmentData.credibility_tier && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  Glaubwürdigkeitsstufe
                </p>
                {getCredibilityBadge(assessmentData.credibility_tier)}
              </div>
            )}

            {/* Reputation Score */}
            {assessmentData.reputation_score !== undefined && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  Reputation Score
                </p>
                <div className="flex items-center gap-2">
                  <Star className="h-4 w-4 text-yellow-500" />
                  <span className="text-base font-semibold">
                    {assessmentData.reputation_score}/100
                  </span>
                </div>
              </div>
            )}

            {/* Political Bias */}
            {assessmentData.political_bias && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  Politische Ausrichtung
                </p>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPoliticalBiasColor(assessmentData.political_bias)}`}>
                  {assessmentData.political_bias.replace(/_/g, ' ')}
                </span>
              </div>
            )}

            {/* Founded Year */}
            {assessmentData.founded_year && (
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">
                  Gegründet
                </p>
                <p className="text-base font-semibold">{assessmentData.founded_year}</p>
              </div>
            )}
          </div>

          {/* Organization Details */}
          {assessmentData.organization_type && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">
                Organisationstyp
              </p>
              <p className="text-base">{assessmentData.organization_type.replace(/_/g, ' ')}</p>
            </div>
          )}

          {/* Editorial Standards */}
          {assessmentData.editorial_standards && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-3">
                Redaktionelle Standards
              </p>
              <div className="grid grid-cols-3 gap-4">
                {assessmentData.editorial_standards.fact_checking_level && (
                  <div>
                    <p className="text-xs text-muted-foreground">Faktencheck-Level</p>
                    <p className="text-sm mt-1 capitalize">
                      {assessmentData.editorial_standards.fact_checking_level}
                    </p>
                  </div>
                )}
                {assessmentData.editorial_standards.corrections_policy && (
                  <div>
                    <p className="text-xs text-muted-foreground">Korrektur-Richtlinien</p>
                    <p className="text-sm mt-1 capitalize">
                      {assessmentData.editorial_standards.corrections_policy}
                    </p>
                  </div>
                )}
                {assessmentData.editorial_standards.source_attribution && (
                  <div>
                    <p className="text-xs text-muted-foreground">Quellenangabe</p>
                    <p className="text-sm mt-1 capitalize">
                      {assessmentData.editorial_standards.source_attribution}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {assessmentData.recommendation && (
            <div className="bg-green-50 dark:bg-green-950/30 p-4 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-start gap-2">
                <Shield className="h-5 w-5 text-green-500 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900 dark:text-green-100 mb-2">
                    Empfehlungen
                  </p>
                  <div className="space-y-1 text-xs text-green-800 dark:text-green-200">
                    {assessmentData.recommendation.skip_waiting_period && (
                      <p>• Wartezeit überspringen aktiviert</p>
                    )}
                    {assessmentData.recommendation.initial_quality_boost !== undefined && (
                      <p>• Initiale Qualitätsverbesserung: +{assessmentData.recommendation.initial_quality_boost}</p>
                    )}
                    {assessmentData.recommendation.bot_detection_threshold !== undefined && (
                      <p>• Bot-Erkennungs-Schwellenwert: {(assessmentData.recommendation.bot_detection_threshold * 100).toFixed(0)}%</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* No Assessment Yet */}
      {!assessmentData && !isAssessing && !assessmentError && (
        <div className="text-center py-8 border-2 border-dashed border-border rounded-lg">
          <Info className="h-12 w-12 mx-auto mb-3 opacity-50 text-muted-foreground" />
          <p className="text-base font-medium text-muted-foreground">
            Noch keine Assessment-Daten verfügbar
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            Führen Sie ein Assessment durch, um automatisch Informationen zu erhalten
          </p>
        </div>
      )}
    </div>
  );
}
