import type { UseFormReturn } from 'react-hook-form';
import { FileCode, Globe } from 'lucide-react';
import type { CreateFeedFormData } from '../types/createFeed';

interface ScrapingOptionsStepProps {
  form: UseFormReturn<CreateFeedFormData, any, any>;
}

export function ScrapingOptionsStep({ form }: ScrapingOptionsStepProps) {
  const { register, watch, setValue } = form;
  const scrapeFullContent = watch('scrape_full_content');
  const scrapeMethod = watch('scrape_method');

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-2">Scraping-Einstellungen</h3>
        <p className="text-sm text-muted-foreground">
          Konfigurieren Sie, wie der vollständige Artikel-Content abgerufen werden soll.
        </p>
      </div>

      {/* Enable Full Content Scraping */}
      <div className="p-4 rounded-lg border border-border">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 mt-1">
            <Globe className={`h-5 w-5 ${scrapeFullContent ? 'text-primary' : 'text-muted-foreground'}`} />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <label htmlFor="scrape_full_content" className="text-sm font-medium cursor-pointer">
                Vollständigen Content scrapen
              </label>
              <input
                id="scrape_full_content"
                type="checkbox"
                {...register('scrape_full_content')}
                className="h-4 w-4"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Wenn aktiviert, wird versucht, den vollständigen Artikel-Text von der Webseite zu extrahieren.
              Deaktivieren Sie diese Option, wenn Sie nur die RSS-Feed-Daten verwenden möchten.
            </p>
          </div>
        </div>
      </div>

      {/* Scraping Method (only visible if scraping is enabled) */}
      {scrapeFullContent && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-3">Scraping-Methode</label>
            <div className="space-y-3">
              {/* Newspaper4k Option */}
              <div
                onClick={() => setValue('scrape_method', 'newspaper4k')}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                  scrapeMethod === 'newspaper4k'
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    value="newspaper4k"
                    checked={scrapeMethod === 'newspaper4k'}
                    onChange={() => setValue('scrape_method', 'newspaper4k')}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <FileCode className="h-4 w-4" />
                      <span className="font-medium">Newspaper4k</span>
                      <span className="text-xs px-2 py-0.5 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 rounded">
                        Empfohlen
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Schnelle, effiziente Python-Library für Article-Scraping.
                      Funktioniert mit den meisten Webseiten ohne JavaScript.
                    </p>
                  </div>
                </div>
              </div>

              {/* Playwright Option */}
              <div
                onClick={() => setValue('scrape_method', 'playwright')}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                  scrapeMethod === 'playwright'
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    value="playwright"
                    checked={scrapeMethod === 'playwright'}
                    onChange={() => setValue('scrape_method', 'playwright')}
                    className="mt-1"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Globe className="h-4 w-4" />
                      <span className="font-medium">Playwright</span>
                      <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded">
                        Experimentell
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Browser-Automation für JavaScript-lastige Webseiten.
                      Langsamer, aber funktioniert mit dynamischem Content.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Failure Threshold */}
          <div>
            <label htmlFor="scrape_failure_threshold" className="block text-sm font-medium mb-2">
              Fehler-Schwellenwert
            </label>
            <div className="flex items-center gap-4">
              <input
                id="scrape_failure_threshold"
                type="range"
                min="1"
                max="20"
                {...register('scrape_failure_threshold', { valueAsNumber: true })}
                className="flex-1"
              />
              <span className="text-sm font-medium min-w-[60px]">
                {watch('scrape_failure_threshold')} Fehler
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Nach wie vielen aufeinanderfolgenden Fehlern soll das Scraping automatisch deaktiviert werden?
            </p>
          </div>
        </div>
      )}

      {/* Info Box */}
      {!scrapeFullContent && (
        <div className="bg-yellow-50 dark:bg-yellow-950/30 p-4 rounded-lg border border-yellow-200 dark:border-yellow-800">
          <p className="text-sm text-yellow-900 dark:text-yellow-100">
            <strong>Hinweis:</strong> Ohne Content-Scraping werden nur die Daten aus dem RSS-Feed verwendet.
            Dies kann zu kürzeren oder unvollständigen Artikel-Texten führen.
          </p>
        </div>
      )}
    </div>
  );
}
