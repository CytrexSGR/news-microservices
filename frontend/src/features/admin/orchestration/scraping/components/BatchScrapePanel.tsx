import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useBatchScrape, useBulkEnqueue } from '../api';
import type { ScrapingMethod, QueuePriority } from '../types/scraping.types';

interface BatchScrapePanelProps {
  className?: string;
}

/**
 * Batch Scrape Panel
 *
 * Panel for batch scraping multiple URLs at once.
 */
export const BatchScrapePanel: React.FC<BatchScrapePanelProps> = ({ className }) => {
  const [urlsText, setUrlsText] = useState('');
  const [method, setMethod] = useState<ScrapingMethod>('auto');
  const [useProxy, setUseProxy] = useState(false);
  const [maxConcurrent, setMaxConcurrent] = useState(5);
  const [mode, setMode] = useState<'immediate' | 'queue'>('queue');
  const [priority, setPriority] = useState<QueuePriority>('NORMAL');
  const [result, setResult] = useState<{
    total: number;
    successful: number;
    failed: number;
    job_ids?: string[];
  } | null>(null);

  const batchScrape = useBatchScrape();
  const bulkEnqueue = useBulkEnqueue();

  const isLoading = batchScrape.isPending || bulkEnqueue.isPending;

  const parseUrls = (): string[] => {
    return urlsText
      .split('\n')
      .map((url) => url.trim())
      .filter((url) => url.startsWith('http'));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setResult(null);

    const urls = parseUrls();
    if (urls.length === 0) {
      alert('Please enter at least one valid URL');
      return;
    }

    try {
      if (mode === 'immediate') {
        const res = await batchScrape.mutateAsync({
          urls,
          method,
          use_proxy: useProxy,
          max_concurrent: maxConcurrent,
        });
        setResult({
          total: res.total,
          successful: res.successful,
          failed: res.failed,
        });
      } else {
        const res = await bulkEnqueue.mutateAsync({ urls, priority });
        setResult({
          total: res.enqueued,
          successful: res.enqueued,
          failed: 0,
          job_ids: res.job_ids,
        });
      }
    } catch (err) {
      console.error('Batch operation failed:', err);
    }
  };

  const urlCount = parseUrls().length;

  return (
    <Card className={className}>
      <form onSubmit={handleSubmit} className="p-6">
        <h3 className="text-lg font-semibold mb-6">Batch Scrape</h3>

        <div className="space-y-4">
          {/* URLs Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              URLs (one per line) *
            </label>
            <textarea
              value={urlsText}
              onChange={(e) => setUrlsText(e.target.value)}
              rows={8}
              placeholder="https://example.com/article1
https://example.com/article2
https://example.com/article3"
              className="w-full px-3 py-2 border rounded font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              {urlCount} valid URL{urlCount !== 1 ? 's' : ''} detected
            </p>
          </div>

          {/* Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Processing Mode
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMode('queue')}
                className={`px-4 py-2 rounded text-sm ${
                  mode === 'queue'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                Add to Queue
              </button>
              <button
                type="button"
                onClick={() => setMode('immediate')}
                className={`px-4 py-2 rounded text-sm ${
                  mode === 'immediate'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                Scrape Immediately
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {mode === 'queue'
                ? 'URLs will be added to the scraping queue for background processing'
                : 'URLs will be scraped immediately (blocks until complete)'}
            </p>
          </div>

          {/* Queue Mode Options */}
          {mode === 'queue' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as QueuePriority)}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="LOW">Low</option>
                <option value="NORMAL">Normal</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>
          )}

          {/* Immediate Mode Options */}
          {mode === 'immediate' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Scraping Method
                  </label>
                  <select
                    value={method}
                    onChange={(e) => setMethod(e.target.value as ScrapingMethod)}
                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="auto">Auto</option>
                    <option value="httpx">HTTPX</option>
                    <option value="playwright">Playwright</option>
                    <option value="newspaper4k">Newspaper4k</option>
                    <option value="trafilatura">Trafilatura</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Concurrent
                  </label>
                  <input
                    type="number"
                    value={maxConcurrent}
                    onChange={(e) => setMaxConcurrent(parseInt(e.target.value) || 5)}
                    min={1}
                    max={20}
                    className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="batchUseProxy"
                  checked={useProxy}
                  onChange={(e) => setUseProxy(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="batchUseProxy" className="text-sm text-gray-700">
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
            disabled={isLoading || urlCount === 0}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading
              ? 'Processing...'
              : mode === 'queue'
              ? `Add ${urlCount} URL${urlCount !== 1 ? 's' : ''} to Queue`
              : `Scrape ${urlCount} URL${urlCount !== 1 ? 's' : ''} Now`}
          </button>
        </div>

        {/* Result */}
        {result && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-semibold mb-3">Result</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white rounded p-3">
                <p className="text-xs text-gray-500">Total</p>
                <p className="text-2xl font-bold">{result.total}</p>
              </div>
              <div className="bg-white rounded p-3">
                <p className="text-xs text-gray-500">Successful</p>
                <p className="text-2xl font-bold text-green-600">{result.successful}</p>
              </div>
              <div className="bg-white rounded p-3">
                <p className="text-xs text-gray-500">Failed</p>
                <p className="text-2xl font-bold text-red-600">{result.failed}</p>
              </div>
            </div>
            {result.job_ids && result.job_ids.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-gray-500 mb-2">Job IDs:</p>
                <div className="bg-white rounded p-2 max-h-32 overflow-y-auto font-mono text-xs">
                  {result.job_ids.map((id) => (
                    <p key={id}>{id}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {(batchScrape.error || bulkEnqueue.error) && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded text-sm">
            {(batchScrape.error || bulkEnqueue.error)?.message}
          </div>
        )}
      </form>
    </Card>
  );
};
