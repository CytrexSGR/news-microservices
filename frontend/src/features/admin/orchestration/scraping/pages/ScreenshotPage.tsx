import React from 'react';
import { ScreenshotTool } from '../components/ScreenshotTool';
import { Card } from '@/components/ui/Card';

/**
 * Screenshot Page
 *
 * Page for capturing screenshots, previews, and PDFs of web pages.
 */
export const ScreenshotPage: React.FC = () => {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Screenshot Tool</h1>
          <p className="text-gray-600">
            Capture screenshots, previews, and PDFs of web pages
          </p>
        </div>
      </div>

      {/* Main Tool */}
      <ScreenshotTool />

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="font-semibold mb-2">Full Page Screenshot</h3>
            <p className="text-sm text-gray-600">
              Capture the entire page from top to bottom, including content below
              the fold. Perfect for archiving or documentation.
            </p>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
            </div>
            <h3 className="font-semibold mb-2">Quick Preview</h3>
            <p className="text-sm text-gray-600">
              Generate a fast thumbnail preview of a page. Useful for visual
              verification and content previews.
            </p>
          </div>
        </Card>

        <Card>
          <div className="p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4">
              <svg
                className="w-6 h-6 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="font-semibold mb-2">PDF Export</h3>
            <p className="text-sm text-gray-600">
              Convert web pages to PDF format for offline reading, printing, or
              archival purposes.
            </p>
          </div>
        </Card>
      </div>

      {/* Tips Section */}
      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Tips for Best Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Viewport Settings</h4>
              <ul className="space-y-1 text-gray-600">
                <li>- Desktop: 1920x1080 (default)</li>
                <li>- Tablet: 768x1024</li>
                <li>- Mobile: 375x667</li>
                <li>- Custom dimensions for specific needs</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Best Practices</h4>
              <ul className="space-y-1 text-gray-600">
                <li>- Wait for page load completion</li>
                <li>- Consider cookie consent modals</li>
                <li>- Some sites may block automated access</li>
                <li>- Use proxy rotation for blocked domains</li>
              </ul>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ScreenshotPage;
