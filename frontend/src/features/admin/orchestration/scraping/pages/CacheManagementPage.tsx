import React, { useState } from 'react';
import { CacheStatsPanel } from '../components/CacheStatsPanel';
import { Card } from '@/components/ui/Card';
import {
  useCacheStats,
  useCachedContent,
  useInvalidateCache,
  useWarmCache,
} from '../api';

/**
 * Cache Lookup Tool
 */
const CacheLookupTool: React.FC = () => {
  const [url, setUrl] = useState('');
  const [lookupUrl, setLookupUrl] = useState('');

  const { data, isLoading, error, refetch } = useCachedContent(lookupUrl);

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    setLookupUrl(url);
  };

  return (
    <Card>
      <div className="p-6">
        <h3 className="font-semibold mb-4">Cache Lookup</h3>
        <form onSubmit={handleLookup} className="flex gap-2 mb-4">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            className="flex-1 px-3 py-2 border rounded"
          />
          <button
            type="submit"
            disabled={isLoading || !url}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading ? 'Looking up...' : 'Lookup'}
          </button>
        </form>

        {error && (
          <p className="text-red-500 text-sm">{error.message}</p>
        )}

        {lookupUrl && !isLoading && !data && (
          <p className="text-gray-500 text-sm">Not found in cache</p>
        )}

        {data && (
          <div className="space-y-3 p-4 bg-gray-50 rounded">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Domain</p>
                <p className="font-medium">{data.domain}</p>
              </div>
              <div>
                <p className="text-gray-500">Size</p>
                <p className="font-medium">{(data.size_bytes / 1024).toFixed(1)} KB</p>
              </div>
              <div>
                <p className="text-gray-500">Cached At</p>
                <p className="font-medium">
                  {new Date(data.cached_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Expires At</p>
                <p className="font-medium">
                  {new Date(data.expires_at).toLocaleString()}
                </p>
              </div>
            </div>
            {data.title && (
              <div>
                <p className="text-gray-500 text-sm">Title</p>
                <p className="font-medium">{data.title}</p>
              </div>
            )}
            {data.author && (
              <div>
                <p className="text-gray-500 text-sm">Author</p>
                <p>{data.author}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};

/**
 * Cache Warming Tool
 */
const CacheWarmingTool: React.FC = () => {
  const [urlsText, setUrlsText] = useState('');
  const warmCache = useWarmCache();

  const handleWarm = async () => {
    const urls = urlsText
      .split('\n')
      .map((u) => u.trim())
      .filter((u) => u.startsWith('http'));

    if (urls.length === 0) {
      alert('Please enter at least one valid URL');
      return;
    }

    try {
      const result = await warmCache.mutateAsync(urls);
      alert(`Warmed ${result.warmed} URLs, ${result.failed} failed`);
      setUrlsText('');
    } catch (err) {
      console.error('Failed to warm cache:', err);
    }
  };

  const urlCount = urlsText
    .split('\n')
    .filter((u) => u.trim().startsWith('http')).length;

  return (
    <Card>
      <div className="p-6">
        <h3 className="font-semibold mb-4">Cache Warming</h3>
        <p className="text-sm text-gray-600 mb-3">
          Pre-fetch URLs to populate the cache
        </p>
        <textarea
          value={urlsText}
          onChange={(e) => setUrlsText(e.target.value)}
          rows={6}
          placeholder="https://example.com/article1
https://example.com/article2
https://example.com/article3"
          className="w-full px-3 py-2 border rounded font-mono text-sm mb-3"
        />
        <div className="flex justify-between items-center">
          <p className="text-sm text-gray-500">{urlCount} URLs</p>
          <button
            onClick={handleWarm}
            disabled={warmCache.isPending || urlCount === 0}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          >
            {warmCache.isPending ? 'Warming...' : 'Warm Cache'}
          </button>
        </div>
        {warmCache.error && (
          <p className="text-red-500 text-sm mt-2">{warmCache.error.message}</p>
        )}
      </div>
    </Card>
  );
};

/**
 * Cache Invalidation Tool
 */
const CacheInvalidationTool: React.FC = () => {
  const [mode, setMode] = useState<'url' | 'domain' | 'age'>('url');
  const [url, setUrl] = useState('');
  const [domain, setDomain] = useState('');
  const [hours, setHours] = useState(24);

  const invalidate = useInvalidateCache();

  const handleInvalidate = async () => {
    let confirmed = false;

    if (mode === 'url') {
      confirmed = confirm(`Invalidate cache for URL: ${url}?`);
      if (confirmed) {
        await invalidate.mutateAsync({ url });
      }
    } else if (mode === 'domain') {
      confirmed = confirm(`Invalidate ALL cache for domain: ${domain}?`);
      if (confirmed) {
        await invalidate.mutateAsync({ domain });
      }
    } else if (mode === 'age') {
      confirmed = confirm(`Invalidate cache older than ${hours} hours?`);
      if (confirmed) {
        await invalidate.mutateAsync({ older_than_hours: hours });
      }
    }

    if (confirmed) {
      alert('Cache invalidated');
      setUrl('');
      setDomain('');
    }
  };

  return (
    <Card>
      <div className="p-6">
        <h3 className="font-semibold mb-4">Cache Invalidation</h3>

        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setMode('url')}
            className={`px-3 py-1 rounded text-sm ${
              mode === 'url' ? 'bg-blue-500 text-white' : 'bg-gray-100'
            }`}
          >
            By URL
          </button>
          <button
            onClick={() => setMode('domain')}
            className={`px-3 py-1 rounded text-sm ${
              mode === 'domain' ? 'bg-blue-500 text-white' : 'bg-gray-100'
            }`}
          >
            By Domain
          </button>
          <button
            onClick={() => setMode('age')}
            className={`px-3 py-1 rounded text-sm ${
              mode === 'age' ? 'bg-blue-500 text-white' : 'bg-gray-100'
            }`}
          >
            By Age
          </button>
        </div>

        {mode === 'url' && (
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            className="w-full px-3 py-2 border rounded mb-3"
          />
        )}

        {mode === 'domain' && (
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="example.com"
            className="w-full px-3 py-2 border rounded mb-3"
          />
        )}

        {mode === 'age' && (
          <div className="mb-3">
            <label className="block text-sm text-gray-600 mb-1">
              Older than (hours)
            </label>
            <input
              type="number"
              value={hours}
              onChange={(e) => setHours(parseInt(e.target.value) || 24)}
              min={1}
              max={720}
              className="w-full px-3 py-2 border rounded"
            />
          </div>
        )}

        <button
          onClick={handleInvalidate}
          disabled={
            invalidate.isPending ||
            (mode === 'url' && !url) ||
            (mode === 'domain' && !domain)
          }
          className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
        >
          {invalidate.isPending ? 'Invalidating...' : 'Invalidate'}
        </button>

        {invalidate.error && (
          <p className="text-red-500 text-sm mt-2">{invalidate.error.message}</p>
        )}
      </div>
    </Card>
  );
};

/**
 * Cache Management Page
 *
 * Page for managing the scraping cache.
 */
export const CacheManagementPage: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Cache Management</h1>
          <p className="text-gray-600">
            Monitor and manage the scraping cache
          </p>
        </div>
      </div>

      {/* Cache Stats */}
      <CacheStatsPanel />

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <CacheLookupTool />
        <CacheWarmingTool />
        <CacheInvalidationTool />
      </div>
    </div>
  );
};

export default CacheManagementPage;
