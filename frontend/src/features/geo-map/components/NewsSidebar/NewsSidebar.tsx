import { useGeoMapStore } from '../../store/geoMapStore';
import { useCountryDetail, useCountryArticles } from '../../hooks/useGeoData';
import { SidebarHeader } from './SidebarHeader';
import { ArticleCard } from './ArticleCard';

export function NewsSidebar() {
  const { selectedCountry, setSelectedCountry } = useGeoMapStore();
  const { data: country, isLoading: loadingCountry } = useCountryDetail(selectedCountry);
  const { data: articles, isLoading: loadingArticles } = useCountryArticles(selectedCountry);

  if (!selectedCountry) return null;

  const isLoading = loadingCountry || loadingArticles;
  const articleList = articles || [];

  return (
    <div className="w-96 bg-white border-l border-gray-200 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <SidebarHeader
        country={country}
        isLoading={loadingCountry}
        onClose={() => setSelectedCountry(null)}
      />

      {/* Article List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : articleList.length > 0 ? (
          articleList.map((article: { id: string; title: string; source?: string; published_at?: string }) => (
            <ArticleCard key={article.id} article={article} />
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>No articles found for this country</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <span className="text-sm text-gray-600">
          {articleList.length} article{articleList.length !== 1 ? 's' : ''} found
        </span>
      </div>
    </div>
  );
}
