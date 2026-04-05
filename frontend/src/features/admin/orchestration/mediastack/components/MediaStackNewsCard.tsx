import React from 'react';
import { Card } from '@/components/ui/Card';
import type { MediaStackArticle } from '../types/mediastack.types';

/**
 * Props for MediaStackNewsCard
 */
interface MediaStackNewsCardProps {
  article: MediaStackArticle;
  className?: string;
}

/**
 * Format date to relative time or date string
 */
function formatPublishedDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 60) {
    return `${diffMins}m ago`;
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays < 7) {
    return `${diffDays}d ago`;
  } else {
    return date.toLocaleDateString();
  }
}

/**
 * Get category badge color
 */
function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    general: 'bg-gray-100 text-gray-800',
    business: 'bg-blue-100 text-blue-800',
    entertainment: 'bg-purple-100 text-purple-800',
    health: 'bg-green-100 text-green-800',
    science: 'bg-indigo-100 text-indigo-800',
    sports: 'bg-orange-100 text-orange-800',
    technology: 'bg-cyan-100 text-cyan-800',
  };
  return colors[category.toLowerCase()] || colors.general;
}

/**
 * Get country flag emoji
 */
function getCountryFlag(countryCode: string): string {
  const flags: Record<string, string> = {
    de: 'DE',
    at: 'AT',
    ch: 'CH',
    us: 'US',
    gb: 'GB',
    fr: 'FR',
    nl: 'NL',
    es: 'ES',
    it: 'IT',
  };
  return flags[countryCode.toLowerCase()] || countryCode.toUpperCase();
}

/**
 * MediaStack News Card
 *
 * Displays a single news article from MediaStack with image,
 * title, description, and metadata.
 */
export const MediaStackNewsCard: React.FC<MediaStackNewsCardProps> = ({
  article,
  className,
}) => {
  return (
    <Card className={`overflow-hidden hover:shadow-md transition-shadow ${className || ''}`}>
      <div className="flex flex-col h-full">
        {/* Image */}
        {article.image && (
          <div className="h-40 bg-gray-100 overflow-hidden">
            <img
              src={article.image}
              alt={article.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        )}

        {/* Content */}
        <div className="p-4 flex-1 flex flex-col">
          {/* Meta badges */}
          <div className="flex flex-wrap gap-2 mb-2">
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(
                article.category
              )}`}
            >
              {article.category}
            </span>
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
              {getCountryFlag(article.country)}
            </span>
            <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
              {article.language.toUpperCase()}
            </span>
          </div>

          {/* Title */}
          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-600"
            >
              {article.title}
            </a>
          </h3>

          {/* Description */}
          <p className="text-sm text-gray-600 mb-3 line-clamp-3 flex-1">
            {article.description}
          </p>

          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t">
            <span className="truncate max-w-[60%]" title={article.source}>
              {article.source}
            </span>
            <span>{formatPublishedDate(article.published_at)}</span>
          </div>

          {/* Author */}
          {article.author && (
            <p className="text-xs text-gray-400 mt-1 truncate">
              By {article.author}
            </p>
          )}
        </div>
      </div>
    </Card>
  );
};

export default MediaStackNewsCard;
