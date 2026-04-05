import React, { useState } from 'react';
import { QueueStatsPanel } from '../components/QueueStatsPanel';
import { QueueItemsTable } from '../components/QueueItemsTable';
import { DLQTable } from '../components/DLQTable';
import { useEnqueueJob } from '../api';
import { Card } from '@/components/ui/Card';
import type { QueuePriority, ScrapingMethod } from '../types/scraping.types';

/**
 * Quick Enqueue Form
 */
const QuickEnqueueForm: React.FC = () => {
  const [url, setUrl] = useState('');
  const [priority, setPriority] = useState<QueuePriority>('NORMAL');
  const [method, setMethod] = useState<ScrapingMethod>('auto');

  const enqueue = useEnqueueJob();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const result = await enqueue.mutateAsync({
        url,
        priority,
        method,
      });
      alert(`Job enqueued at position ${result.position}`);
      setUrl('');
    } catch (err) {
      console.error('Failed to enqueue:', err);
    }
  };

  return (
    <Card>
      <form onSubmit={handleSubmit} className="p-4">
        <h3 className="font-semibold mb-3">Quick Enqueue</h3>
        <div className="flex gap-2">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            required
            className="flex-1 px-3 py-2 border rounded text-sm"
          />
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as QueuePriority)}
            className="px-3 py-2 border rounded text-sm"
          >
            <option value="LOW">Low</option>
            <option value="NORMAL">Normal</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as ScrapingMethod)}
            className="px-3 py-2 border rounded text-sm"
          >
            <option value="auto">Auto</option>
            <option value="httpx">HTTPX</option>
            <option value="playwright">Playwright</option>
            <option value="newspaper4k">Newspaper4k</option>
            <option value="trafilatura">Trafilatura</option>
          </select>
          <button
            type="submit"
            disabled={enqueue.isPending || !url}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 text-sm"
          >
            {enqueue.isPending ? 'Adding...' : 'Enqueue'}
          </button>
        </div>
        {enqueue.error && (
          <p className="text-red-500 text-sm mt-2">{enqueue.error.message}</p>
        )}
      </form>
    </Card>
  );
};

/**
 * Queue Management Page
 *
 * Comprehensive queue and DLQ management page.
 */
export const QueueManagementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'queue' | 'dlq'>('queue');

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Queue Management</h1>
          <p className="text-gray-600">
            Manage scraping queue and dead letter queue
          </p>
        </div>
      </div>

      {/* Quick Enqueue */}
      <QuickEnqueueForm />

      {/* Queue Stats */}
      <QueueStatsPanel />

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('queue')}
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'queue'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Active Queue
          </button>
          <button
            onClick={() => setActiveTab('dlq')}
            className={`pb-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'dlq'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Dead Letter Queue
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'queue' ? (
        <QueueItemsTable pageSize={20} />
      ) : (
        <DLQTable pageSize={20} />
      )}
    </div>
  );
};

export default QueueManagementPage;
