import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useDirectScrape, useArticleExtraction, useMetadataExtraction } from '../api';
import type { ScrapingMethod, DirectScrapeResult } from '../types/scraping.types';

interface DirectScrapeFormProps {
  className?: string;
}

/**
 * Result Display
 */
const ResultDisplay: React.FC<{ result: DirectScrapeResult }> = ({ result }) => {
  const [showContent, setShowContent] = useState(false);

  return (
    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
      <div className="flex justify-between items-start mb-4">
        <h4 className="font-semibold">Scrape Result</h4>
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${
            result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}
        >
          {result.success ? 'SUCCESS' : 'FAILED'}
        </span>
      </div>

      {result.success ? (
        <div className="space-y-3">
          {result.title && (
            <div>
              <p className="text-xs text-gray-500">Title</p>
              <p className="font-medium">{result.title}</p>
            </div>
          )}
          {result.author && (
            <div>
              <p className="text-xs text-gray-500">Author</p>
              <p>{result.author}</p>
            </div>
          )}
          {result.published_date && (
            <div>
              <p className="text-xs text-gray-500">Published</p>
              <p>{result.published_date}</p>
            </div>
          )}

          <div className="grid grid-cols-3 gap-4 text-sm">
            <div className="bg-white rounded p-2">
              <p className="text-xs text-gray-500">Method</p>
              <p className="font-medium">{result.method_used}</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="text-xs text-gray-500">Content Length</p>
              <p className="font-medium">{result.content_length.toLocaleString()} chars</p>
            </div>
            <div className="bg-white rounded p-2">
              <p className="text-xs text-gray-500">Scrape Time</p>
              <p className="font-medium">{result.scrape_time_ms}ms</p>
            </div>
          </div>

          {result.content && (
            <div>
              <button
                onClick={() => setShowContent(!showContent)}
                className="text-sm text-blue-600 hover:underline"
              >
                {showContent ? 'Hide Content' : 'Show Content'}
              </button>
              {showContent && (
                <div className="mt-2 p-3 bg-white rounded border max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm">{result.content}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="text-red-600">
          <p className="font-medium">Error:</p>
          <p className="text-sm">{result.error}</p>
        </div>
      )}
    </div>
  );
};

/**
 * Direct Scrape Form
 *
 * Form for directly scraping a URL with various options.
 */
export const DirectScrapeForm: React.FC<DirectScrapeFormProps> = ({ className }) => {
  const [url, setUrl] = useState('');
  const [method, setMethod] = useState<ScrapingMethod>('auto');
  const [useProxy, setUseProxy] = useState(false);
  const [timeout, setTimeout] = useState(30);
  const [result, setResult] = useState<DirectScrapeResult | null>(null);
  const [extractionType, setExtractionType] = useState<'scrape' | 'article' | 'metadata'>('scrape');

  const directScrape = useDirectScrape();
  const articleExtraction = useArticleExtraction();
  const metadataExtraction = useMetadataExtraction();

  const isLoading = directScrape.isPending || articleExtraction.isPending || metadataExtraction.isPending;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);

    try {
      if (extractionType === 'scrape') {
        const res = await directScrape.mutateAsync({
          url,
          method,
          use_proxy: useProxy,
          timeout_seconds: timeout,
        });
        setResult(res);
      } else if (extractionType === 'article') {
        const res = await articleExtraction.mutateAsync(url);
        setResult({
          success: res.success,
          url: res.url,
          domain: new URL(res.url).hostname,
          method_used: 'newspaper4k',
          title: res.title,
          content: res.content,
          author: res.author,
          published_date: res.published_date,
          content_length: res.content?.length || 0,
          scrape_time_ms: res.extraction_time_ms,
          error: res.error,
        });
      } else if (extractionType === 'metadata') {
        const res = await metadataExtraction.mutateAsync(url);
        setResult({
          success: res.success,
          url: res.url,
          domain: new URL(res.url).hostname,
          method_used: 'httpx',
          title: res.title || res.og_title,
          content: JSON.stringify(res, null, 2),
          author: res.author,
          published_date: res.published_date,
          content_length: 0,
          scrape_time_ms: 0,
        });
      }
    } catch (err) {
      console.error('Scrape failed:', err);
    }
  };

  const methodOptions: ScrapingMethod[] = ['auto', 'httpx', 'playwright', 'newspaper4k', 'trafilatura'];

  return (
    <Card className={className}>
      <form onSubmit={handleSubmit} className="p-6">
        <h3 className="text-lg font-semibold mb-6">Direct Scrape</h3>

        <div className="space-y-4">
          {/* URL Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              URL *
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/article"
              required
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Extraction Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Extraction Type
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setExtractionType('scrape')}
                className={`px-3 py-2 rounded text-sm ${
                  extractionType === 'scrape'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                Raw Scrape
              </button>
              <button
                type="button"
                onClick={() => setExtractionType('article')}
                className={`px-3 py-2 rounded text-sm ${
                  extractionType === 'article'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                Article Extraction
              </button>
              <button
                type="button"
                onClick={() => setExtractionType('metadata')}
                className={`px-3 py-2 rounded text-sm ${
                  extractionType === 'metadata'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                Metadata Only
              </button>
            </div>
          </div>

          {/* Options (only for raw scrape) */}
          {extractionType === 'scrape' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Method
                  </label>
                  <select
                    value={method}
                    onChange={(e) => setMethod(e.target.value as ScrapingMethod)}
                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {methodOptions.map((m) => (
                      <option key={m} value={m}>
                        {m.charAt(0).toUpperCase() + m.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={timeout}
                    onChange={(e) => setTimeout(parseInt(e.target.value) || 30)}
                    min={5}
                    max={120}
                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="useProxy"
                  checked={useProxy}
                  onChange={(e) => setUseProxy(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="useProxy" className="text-sm text-gray-700">
                  Use Proxy
                </label>
              </div>
            </>
          )}
        </div>

        {/* Submit */}
        <div className="mt-6">
          <button
            type="submit"
            disabled={isLoading || !url}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading ? 'Scraping...' : 'Scrape URL'}
          </button>
        </div>

        {/* Result */}
        {result && <ResultDisplay result={result} />}

        {/* Error */}
        {(directScrape.error || articleExtraction.error || metadataExtraction.error) && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded text-sm">
            {(directScrape.error || articleExtraction.error || metadataExtraction.error)?.message}
          </div>
        )}
      </form>
    </Card>
  );
};
