import React, { useState } from 'react';
import { DirectScrapeForm } from '../components/DirectScrapeForm';
import { BatchScrapePanel } from '../components/BatchScrapePanel';
import { WikipediaScrapeForm } from '../components/WikipediaScrapeForm';

type ToolTab = 'direct' | 'batch' | 'wikipedia';

/**
 * Scraping Tools Page
 *
 * Page for direct scraping tools including single URL,
 * batch processing, and Wikipedia integration.
 */
export const ScrapingToolsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ToolTab>('direct');

  const tabs: { id: ToolTab; label: string; description: string }[] = [
    {
      id: 'direct',
      label: 'Direct Scrape',
      description: 'Scrape a single URL immediately',
    },
    {
      id: 'batch',
      label: 'Batch Scrape',
      description: 'Process multiple URLs at once',
    },
    {
      id: 'wikipedia',
      label: 'Wikipedia',
      description: 'Search and fetch Wikipedia articles',
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Scraping Tools</h1>
          <p className="text-gray-600">
            Direct scraping utilities for testing and manual operations
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg border">
        <div className="border-b">
          <nav className="flex">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-6 py-4 text-center border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                <p className="font-medium">{tab.label}</p>
                <p className="text-xs text-gray-500 mt-1">{tab.description}</p>
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'direct' && <DirectScrapeForm />}
          {activeTab === 'batch' && <BatchScrapePanel />}
          {activeTab === 'wikipedia' && <WikipediaScrapeForm />}
        </div>
      </div>

      {/* Usage Tips */}
      <div className="bg-gray-50 rounded-lg border p-6">
        <h3 className="font-semibold mb-3">Usage Tips</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Direct Scrape</h4>
            <ul className="space-y-1 text-gray-600">
              <li>- Use for testing scraping configurations</li>
              <li>- Preview content extraction results</li>
              <li>- Debug problematic URLs</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Batch Scrape</h4>
            <ul className="space-y-1 text-gray-600">
              <li>- Process up to 100 URLs at once</li>
              <li>- Choose immediate or queued processing</li>
              <li>- Monitor batch progress in real-time</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Wikipedia</h4>
            <ul className="space-y-1 text-gray-600">
              <li>- Search Wikipedia by keyword</li>
              <li>- Fetch full article content</li>
              <li>- Use for reference data enrichment</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScrapingToolsPage;
