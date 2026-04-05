import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import {
  useWikipediaSearchMutation,
  useWikipediaArticleMutation,
  useWikipediaRelationships,
  useWikipediaSummary,
} from '../api';
import type { WikipediaSearchResult, WikipediaArticle } from '../types/scraping.types';

interface WikipediaScrapeFormProps {
  className?: string;
}

type WikipediaLanguage = 'de' | 'en' | 'fr' | 'es' | 'it';

/**
 * Search Result Item
 */
const SearchResultItem: React.FC<{
  result: WikipediaSearchResult;
  onSelect: (title: string) => void;
}> = ({ result, onSelect }) => (
  <div
    className="p-3 border rounded hover:bg-gray-50 cursor-pointer"
    onClick={() => onSelect(result.title)}
  >
    <h4 className="font-medium text-blue-600">{result.title}</h4>
    <p
      className="text-sm text-gray-600 mt-1"
      dangerouslySetInnerHTML={{ __html: result.snippet }}
    />
  </div>
);

/**
 * Article Display
 */
const ArticleDisplay: React.FC<{ article: WikipediaArticle }> = ({ article }) => {
  const [showFull, setShowFull] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-start">
        <h3 className="text-xl font-semibold">{article.title}</h3>
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:underline"
        >
          Open in Wikipedia
        </a>
      </div>

      <div className="prose prose-sm max-w-none">
        <p>{article.summary}</p>
        {article.content && (
          <>
            <button
              onClick={() => setShowFull(!showFull)}
              className="text-blue-600 hover:underline text-sm"
            >
              {showFull ? 'Show less' : 'Show full article'}
            </button>
            {showFull && (
              <div className="mt-4 p-4 bg-gray-50 rounded max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm">{article.content}</pre>
              </div>
            )}
          </>
        )}
      </div>

      {article.infobox && Object.keys(article.infobox).length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Infobox</h4>
          <div className="bg-gray-50 rounded p-3">
            {Object.entries(article.infobox).map(([key, value]) => (
              <div key={key} className="flex gap-2 text-sm py-1 border-b last:border-0">
                <span className="font-medium text-gray-600 w-32">{key}:</span>
                <span>{Array.isArray(value) ? value.join(', ') : value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {article.categories && article.categories.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Categories</h4>
          <div className="flex flex-wrap gap-2">
            {article.categories.map((cat) => (
              <span key={cat} className="px-2 py-1 bg-gray-100 rounded text-sm">
                {cat}
              </span>
            ))}
          </div>
        </div>
      )}

      {article.images && article.images.length > 0 && (
        <div>
          <h4 className="font-medium mb-2">Images ({article.images.length})</h4>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {article.images.slice(0, 5).map((img, i) => (
              <img
                key={i}
                src={img}
                alt=""
                className="h-24 w-auto rounded border"
                onError={(e) => (e.currentTarget.style.display = 'none')}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Wikipedia Scrape Form
 *
 * Form for searching and fetching Wikipedia articles.
 */
export const WikipediaScrapeForm: React.FC<WikipediaScrapeFormProps> = ({ className }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [language, setLanguage] = useState<WikipediaLanguage>('de');
  const [searchResults, setSearchResults] = useState<WikipediaSearchResult[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<WikipediaArticle | null>(null);
  const [includeInfobox, setIncludeInfobox] = useState(true);
  const [includeCategories, setIncludeCategories] = useState(true);

  const search = useWikipediaSearchMutation();
  const fetchArticle = useWikipediaArticleMutation();
  const fetchRelationships = useWikipediaRelationships();
  const fetchSummary = useWikipediaSummary();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setSelectedArticle(null);

    try {
      const result = await search.mutateAsync({
        query: searchQuery,
        language,
        limit: 10,
      });
      setSearchResults(result.results);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const handleSelectResult = async (title: string) => {
    try {
      const article = await fetchArticle.mutateAsync({
        title,
        language,
        include_infobox: includeInfobox,
        include_categories: includeCategories,
        include_links: true,
      });
      setSelectedArticle(article);
      setSearchResults([]);
    } catch (err) {
      console.error('Failed to fetch article:', err);
    }
  };

  const handleFetchRelationships = async () => {
    if (!selectedArticle) return;
    try {
      const result = await fetchRelationships.mutateAsync({
        title: selectedArticle.title,
        language,
      });
      alert(`Found ${result.total} relationships`);
    } catch (err) {
      console.error('Failed to fetch relationships:', err);
    }
  };

  const isLoading = search.isPending || fetchArticle.isPending;

  return (
    <Card className={className}>
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-6">Wikipedia Scraper</h3>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="space-y-4 mb-6">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search Wikipedia..."
              className="flex-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as WikipediaLanguage)}
              className="px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="de">Deutsch</option>
              <option value="en">English</option>
              <option value="fr">Francais</option>
              <option value="es">Espanol</option>
              <option value="it">Italiano</option>
            </select>
            <button
              type="submit"
              disabled={isLoading || !searchQuery}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {search.isPending ? 'Searching...' : 'Search'}
            </button>
          </div>

          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeInfobox}
                onChange={(e) => setIncludeInfobox(e.target.checked)}
                className="rounded"
              />
              Include Infobox
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeCategories}
                onChange={(e) => setIncludeCategories(e.target.checked)}
                className="rounded"
              />
              Include Categories
            </label>
          </div>
        </form>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="space-y-2 mb-6">
            <h4 className="font-medium text-gray-700">Search Results</h4>
            {searchResults.map((result) => (
              <SearchResultItem
                key={result.pageid}
                result={result}
                onSelect={handleSelectResult}
              />
            ))}
          </div>
        )}

        {/* Loading */}
        {fetchArticle.isPending && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-500 mt-2">Loading article...</p>
          </div>
        )}

        {/* Selected Article */}
        {selectedArticle && (
          <div className="border-t pt-6">
            <div className="flex justify-between items-center mb-4">
              <button
                onClick={() => {
                  setSelectedArticle(null);
                  setSearchResults([]);
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                &larr; Back to search
              </button>
              <button
                onClick={handleFetchRelationships}
                disabled={fetchRelationships.isPending}
                className="px-3 py-1 text-sm bg-purple-100 text-purple-700 rounded hover:bg-purple-200 disabled:opacity-50"
              >
                {fetchRelationships.isPending ? 'Loading...' : 'Extract Relationships'}
              </button>
            </div>
            <ArticleDisplay article={selectedArticle} />
          </div>
        )}

        {/* Errors */}
        {(search.error || fetchArticle.error) && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded text-sm">
            {(search.error || fetchArticle.error)?.message}
          </div>
        )}
      </div>
    </Card>
  );
};
