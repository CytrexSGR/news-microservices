import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { useCreateSourceProfile, useUpdateSourceProfile } from '../api';
import type { SourceProfile, ScrapingMethod } from '../types/scraping.types';

interface SourceProfileFormProps {
  className?: string;
  profile?: SourceProfile;
  onSuccess?: () => void;
  onCancel?: () => void;
}

/**
 * Source Profile Form
 *
 * Form for creating or editing source profiles.
 */
export const SourceProfileForm: React.FC<SourceProfileFormProps> = ({
  className,
  profile,
  onSuccess,
  onCancel,
}) => {
  const isEditMode = !!profile;

  const [formData, setFormData] = useState({
    domain: profile?.domain || '',
    scraping_method: profile?.scraping_method || 'auto' as ScrapingMethod,
    requires_js: profile?.requires_js || false,
    requires_proxy: profile?.requires_proxy || false,
    rate_limit_rpm: profile?.rate_limit_rpm || 60,
    title_selector: profile?.custom_selectors?.title || '',
    content_selector: profile?.custom_selectors?.content || '',
    author_selector: profile?.custom_selectors?.author || '',
    date_selector: profile?.custom_selectors?.date || '',
    notes: profile?.notes || '',
  });

  const createProfile = useCreateSourceProfile();
  const updateProfile = useUpdateSourceProfile();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const custom_selectors = {
      title: formData.title_selector || undefined,
      content: formData.content_selector || undefined,
      author: formData.author_selector || undefined,
      date: formData.date_selector || undefined,
    };

    const hasSelectors = Object.values(custom_selectors).some(Boolean);

    const params = {
      domain: formData.domain,
      scraping_method: formData.scraping_method,
      requires_js: formData.requires_js,
      requires_proxy: formData.requires_proxy,
      rate_limit_rpm: formData.rate_limit_rpm,
      custom_selectors: hasSelectors ? custom_selectors : undefined,
      notes: formData.notes || undefined,
    };

    try {
      if (isEditMode) {
        await updateProfile.mutateAsync(params);
      } else {
        await createProfile.mutateAsync(params);
      }
      onSuccess?.();
    } catch (err) {
      console.error('Failed to save profile:', err);
    }
  };

  const methodOptions: ScrapingMethod[] = ['auto', 'httpx', 'playwright', 'newspaper4k', 'trafilatura'];

  const isLoading = createProfile.isPending || updateProfile.isPending;
  const error = createProfile.error || updateProfile.error;

  return (
    <Card className={className}>
      <form onSubmit={handleSubmit} className="p-6">
        <h3 className="text-lg font-semibold mb-6">
          {isEditMode ? 'Edit Source Profile' : 'Create Source Profile'}
        </h3>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">
            {error.message}
          </div>
        )}

        <div className="space-y-4">
          {/* Domain */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domain *
            </label>
            <input
              type="text"
              value={formData.domain}
              onChange={(e) => setFormData((f) => ({ ...f, domain: e.target.value }))}
              placeholder="example.com"
              disabled={isEditMode}
              required
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
          </div>

          {/* Scraping Method */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scraping Method
            </label>
            <select
              value={formData.scraping_method}
              onChange={(e) =>
                setFormData((f) => ({ ...f, scraping_method: e.target.value as ScrapingMethod }))
              }
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {methodOptions.map((method) => (
                <option key={method} value={method}>
                  {method.charAt(0).toUpperCase() + method.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Options Row */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="requires_js"
                checked={formData.requires_js}
                onChange={(e) =>
                  setFormData((f) => ({ ...f, requires_js: e.target.checked }))
                }
                className="rounded"
              />
              <label htmlFor="requires_js" className="text-sm text-gray-700">
                Requires JavaScript
              </label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="requires_proxy"
                checked={formData.requires_proxy}
                onChange={(e) =>
                  setFormData((f) => ({ ...f, requires_proxy: e.target.checked }))
                }
                className="rounded"
              />
              <label htmlFor="requires_proxy" className="text-sm text-gray-700">
                Requires Proxy
              </label>
            </div>
          </div>

          {/* Rate Limit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rate Limit (requests/minute)
            </label>
            <input
              type="number"
              value={formData.rate_limit_rpm}
              onChange={(e) =>
                setFormData((f) => ({ ...f, rate_limit_rpm: parseInt(e.target.value) || 60 }))
              }
              min={1}
              max={1000}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Custom Selectors */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Custom Selectors (optional)</h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Title</label>
                <input
                  type="text"
                  value={formData.title_selector}
                  onChange={(e) =>
                    setFormData((f) => ({ ...f, title_selector: e.target.value }))
                  }
                  placeholder="h1.article-title"
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Content</label>
                <input
                  type="text"
                  value={formData.content_selector}
                  onChange={(e) =>
                    setFormData((f) => ({ ...f, content_selector: e.target.value }))
                  }
                  placeholder="article.content"
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Author</label>
                <input
                  type="text"
                  value={formData.author_selector}
                  onChange={(e) =>
                    setFormData((f) => ({ ...f, author_selector: e.target.value }))
                  }
                  placeholder="span.author-name"
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Date</label>
                <input
                  type="text"
                  value={formData.date_selector}
                  onChange={(e) =>
                    setFormData((f) => ({ ...f, date_selector: e.target.value }))
                  }
                  placeholder="time.published"
                  className="w-full px-2 py-1 border rounded text-sm"
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData((f) => ({ ...f, notes: e.target.value }))}
              rows={3}
              placeholder="Any notes about this source..."
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border rounded hover:bg-gray-50"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isLoading || !formData.domain}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading ? 'Saving...' : isEditMode ? 'Update Profile' : 'Create Profile'}
          </button>
        </div>
      </form>
    </Card>
  );
};
