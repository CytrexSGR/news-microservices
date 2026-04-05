import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { X, ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { FeedBasicInfoStep } from './FeedBasicInfoStep';
import { FeedAssessmentStep } from './FeedAssessmentStep';
import { FeedAnalysisOptions } from './FeedAnalysisOptions';
import { ScrapingOptionsStep } from './ScrapingOptionsStep';
import { useCreateFeed } from '../api/useCreateFeed';
import { usePreAssessFeed } from '../api/usePreAssessFeed';
import { createFeedSchema } from '../schemas/createFeedSchema';
import { DEFAULT_FEED_VALUES, type CreateFeedFormData, type PreAssessmentResponse } from '../types/createFeed';

interface CreateFeedDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const STEPS = [
  { id: 1, title: 'Grundinformationen', description: 'Feed URL und Basis-Daten' },
  { id: 2, title: 'Source Assessment', description: 'Optional: Quelle bewerten' },
  { id: 3, title: 'Analysis Optionen', description: 'Auto-Analyse konfigurieren' },
  { id: 4, title: 'Scraping', description: 'Content-Scraping einstellen' },
];

export function CreateFeedDialog({ open, onClose, onSuccess }: CreateFeedDialogProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [assessmentData, setAssessmentData] = useState<PreAssessmentResponse['assessment']>();

  const form = useForm<CreateFeedFormData>({
    resolver: zodResolver(createFeedSchema) as any,
    defaultValues: DEFAULT_FEED_VALUES,
  });

  const createFeedMutation = useCreateFeed();
  const preAssessmentMutation = usePreAssessFeed();

  // Reset form and state when dialog opens/closes
  useEffect(() => {
    if (open) {
      form.reset(DEFAULT_FEED_VALUES);
      setCurrentStep(1);
      setAssessmentData(undefined);
    }
  }, [open, form]);

  const handleRunAssessment = async () => {
    const url = form.getValues('url');
    if (!url) return;

    try {
      const result = await preAssessmentMutation.mutateAsync({ url });

      // Store assessment data
      setAssessmentData(result.assessment);

      // Auto-fill form fields with suggested values
      if (result.suggested_values) {
        // Name: Only fill if empty
        if (result.suggested_values.name && !form.getValues('name')) {
          form.setValue('name', result.suggested_values.name);
        }
        // Description: ALWAYS override with assessment description (it's much better)
        if (result.suggested_values.description) {
          form.setValue('description', result.suggested_values.description);
        }
        // Category: Always use assessment category (single category from fixed set)
        if (result.suggested_values.category) {
          form.setValue('category', result.suggested_values.category);
        }
      }

      // Mark that assessment was run
      form.setValue('_hasRunAssessment' as any, true);
      form.setValue('_assessmentData' as any, result.assessment);

      // Store assessment data in actual form fields (so they get sent to backend)
      // Only set fields that have actual values (not undefined)
      if (result.assessment) {
        if (result.assessment.credibility_tier !== undefined) {
          form.setValue('credibility_tier', result.assessment.credibility_tier);
        }
        if (result.assessment.reputation_score !== undefined) {
          form.setValue('reputation_score', result.assessment.reputation_score);
        }
        if (result.assessment.founded_year !== undefined) {
          form.setValue('founded_year', result.assessment.founded_year);
        }
        if (result.assessment.organization_type !== undefined) {
          form.setValue('organization_type', result.assessment.organization_type);
        }
        if (result.assessment.political_bias !== undefined) {
          form.setValue('political_bias', result.assessment.political_bias);
        }
        if (result.assessment.editorial_standards !== undefined) {
          form.setValue('editorial_standards', result.assessment.editorial_standards);
        }
        if (result.assessment.trust_ratings !== undefined) {
          form.setValue('trust_ratings', result.assessment.trust_ratings);
        }
        if (result.assessment.recommendation !== undefined) {
          form.setValue('recommendation', result.assessment.recommendation);
        }
        if (result.assessment.assessment_summary !== undefined) {
          form.setValue('assessment_summary', result.assessment.assessment_summary);
        }
      }
    } catch (error) {
      // Error is handled by the mutation hook
    }
  };

  const handleNext = async () => {
    // Validate current step before proceeding
    const fieldsToValidate = getFieldsForStep(currentStep);
    const isValid = await form.trigger(fieldsToValidate);

    if (isValid && currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const getFieldsForStep = (step: number): (keyof CreateFeedFormData)[] => {
    switch (step) {
      case 1:
        return ['url', 'name', 'fetch_interval'];
      case 2:
        return []; // Assessment step has no required fields
      case 3:
        return []; // Analysis options have no validation
      case 4:
        return ['scrape_method', 'scrape_failure_threshold'];
      default:
        return [];
    }
  };

  const onSubmit = async (data: CreateFeedFormData) => {
    // Remove internal fields only (assessment data is now part of FeedCreateInput)
    const { _hasRunAssessment, _assessmentData, ...feedData } = data as any;

    // Helper: Check if object is empty or only has undefined values
    const isEmptyObject = (obj: any) => {
      if (!obj || typeof obj !== 'object') return true;
      return Object.values(obj).every(val => val === undefined || val === null);
    };

    // Clean up nested assessment objects - remove if empty
    if (isEmptyObject(feedData.editorial_standards)) {
      delete feedData.editorial_standards;
    }
    if (isEmptyObject(feedData.trust_ratings)) {
      delete feedData.trust_ratings;
    }
    if (isEmptyObject(feedData.recommendation)) {
      delete feedData.recommendation;
    }

    // Ensure all required boolean fields have explicit values (prevent undefined)
    // This fixes the issue where unchanged toggles don't get sent to backend
    const completeData = {
      ...feedData,
      // Description (CRITICAL: ensure it's included even if undefined)
      description: feedData.description ?? DEFAULT_FEED_VALUES.description,
      // Scraping config (use explicit values or defaults)
      scrape_full_content: feedData.scrape_full_content ?? DEFAULT_FEED_VALUES.scrape_full_content,
      scrape_method: feedData.scrape_method ?? DEFAULT_FEED_VALUES.scrape_method,
      scrape_failure_threshold: feedData.scrape_failure_threshold ?? DEFAULT_FEED_VALUES.scrape_failure_threshold,
      // Analysis flags (use explicit values or defaults)
      enable_categorization: feedData.enable_categorization ?? DEFAULT_FEED_VALUES.enable_categorization,
      enable_finance_sentiment: feedData.enable_finance_sentiment ?? DEFAULT_FEED_VALUES.enable_finance_sentiment,
      enable_geopolitical_sentiment: feedData.enable_geopolitical_sentiment ?? DEFAULT_FEED_VALUES.enable_geopolitical_sentiment,
      enable_osint_analysis: feedData.enable_osint_analysis ?? DEFAULT_FEED_VALUES.enable_osint_analysis,
      enable_summary: feedData.enable_summary ?? DEFAULT_FEED_VALUES.enable_summary,
      enable_entity_extraction: feedData.enable_entity_extraction ?? DEFAULT_FEED_VALUES.enable_entity_extraction,
      enable_topic_classification: feedData.enable_topic_classification ?? DEFAULT_FEED_VALUES.enable_topic_classification,
    };

    try {
      await createFeedMutation.mutateAsync(completeData);

      // Success!
      onSuccess?.();
      onClose();
    } catch (error) {
      // Error is handled by the mutation hook
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <FeedBasicInfoStep
            form={form}
            isAssessmentDataAvailable={!!assessmentData}
          />
        );
      case 2:
        return (
          <FeedAssessmentStep
            form={form}
            assessmentData={assessmentData}
            onRunAssessment={handleRunAssessment}
            isAssessing={preAssessmentMutation.isPending}
            assessmentError={preAssessmentMutation.error}
          />
        );
      case 3:
        return <FeedAnalysisOptions form={form} />;
      case 4:
        return <ScrapingOptionsStep form={form} />;
      default:
        return null;
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-background rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Neuen Feed erstellen</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Schritt {currentStep} von {STEPS.length}: {STEPS[currentStep - 1].description}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-muted rounded-full transition-colors"
            disabled={createFeedMutation.isPending}
            aria-label="Close dialog"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Progress Indicator */}
        <div className="px-6 py-4 border-b border-border">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-colors ${
                      currentStep > step.id
                        ? 'bg-primary text-primary-foreground'
                        : currentStep === step.id
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    {currentStep > step.id ? <Check className="h-5 w-5" /> : step.id}
                  </div>
                  <span className="text-xs mt-2 text-center font-medium hidden sm:block">
                    {step.title}
                  </span>
                </div>
                {index < STEPS.length - 1 && (
                  <div
                    className={`h-1 flex-1 mx-2 rounded transition-colors ${
                      currentStep > step.id ? 'bg-primary' : 'bg-muted'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <form
            id="create-feed-form"
            onSubmit={form.handleSubmit(onSubmit)}
            onKeyDown={(e) => {
              // Prevent Enter key from submitting form (except on final step)
              if (e.key === 'Enter' && currentStep < STEPS.length) {
                e.preventDefault();
              }
            }}
          >
            {renderStepContent()}
          </form>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex items-center justify-between">
          <button
            type="button"
            onClick={handleBack}
            disabled={currentStep === 1 || createFeedMutation.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-foreground bg-muted rounded-md hover:bg-muted/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
            Zurück
          </button>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={createFeedMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Abbrechen
            </button>

            {currentStep < STEPS.length ? (
              <button
                type="button"
                onClick={handleNext}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                Weiter
                <ChevronRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                type="button"
                disabled={createFeedMutation.isPending}
                onClick={() => {
                  // Explicitly trigger form submit
                  form.handleSubmit(onSubmit)();
                }}
                className="inline-flex items-center gap-2 px-6 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {createFeedMutation.isPending ? (
                  <>
                    <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                    Erstelle Feed...
                  </>
                ) : (
                  <>
                    <Check className="h-4 w-4" />
                    Feed erstellen
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Validation Errors Display */}
        {Object.keys(form.formState.errors).length > 0 && (
          <div className="px-6 pb-4">
            <div className="p-3 bg-yellow-50 dark:bg-yellow-950/30 border border-yellow-200 dark:border-yellow-800 rounded-md">
              <p className="text-sm font-medium text-yellow-900 dark:text-yellow-100 mb-2">
                Validierungsfehler:
              </p>
              <ul className="text-xs text-yellow-800 dark:text-yellow-200 space-y-1">
                {Object.entries(form.formState.errors).map(([field, error]) => (
                  <li key={field}>
                    <strong>{field}:</strong> {error?.message as string || 'Ungültig'}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Error Display */}
        {createFeedMutation.error && (
          <div className="px-6 pb-4">
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive">
                Fehler beim Erstellen des Feeds: {(createFeedMutation.error as Error).message}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
