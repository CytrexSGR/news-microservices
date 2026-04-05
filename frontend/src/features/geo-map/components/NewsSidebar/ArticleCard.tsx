interface Article {
  id: string;
  title: string;
  source?: string;
  published_at?: string;
  image_url?: string;
  category?: string;
}

interface Props {
  article: Article;
}

export function ArticleCard({ article }: Props) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer">
      <div className="flex gap-3">
        {article.image_url && (
          <img
            src={article.image_url}
            alt=""
            className="w-20 h-16 object-cover rounded flex-shrink-0"
          />
        )}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
            {article.title}
          </h3>
          <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
            {article.source && <span>{article.source}</span>}
            {article.published_at && (
              <>
                <span>-</span>
                <span>{formatDate(article.published_at)}</span>
              </>
            )}
          </div>
          {article.category && (
            <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">
              {article.category}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
