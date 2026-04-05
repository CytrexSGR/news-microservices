import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { useScreenshot, usePreview, usePdf } from '../api';

interface ScreenshotToolProps {
  className?: string;
}

type ScreenshotFormat = 'png' | 'jpeg' | 'webp';
type PdfFormat = 'A4' | 'Letter' | 'Legal';
type ToolMode = 'screenshot' | 'preview' | 'pdf';

/**
 * Screenshot Tool
 *
 * Tool for capturing screenshots, generating previews, and creating PDFs from URLs.
 */
export const ScreenshotTool: React.FC<ScreenshotToolProps> = ({ className }) => {
  const [url, setUrl] = useState('');
  const [mode, setMode] = useState<ToolMode>('screenshot');

  // Screenshot options
  const [fullPage, setFullPage] = useState(false);
  const [format, setFormat] = useState<ScreenshotFormat>('png');
  const [quality, setQuality] = useState(90);
  const [width, setWidth] = useState(1280);
  const [height, setHeight] = useState(720);
  const [waitSeconds, setWaitSeconds] = useState(2);
  const [selector, setSelector] = useState('');

  // PDF options
  const [pdfFormat, setPdfFormat] = useState<PdfFormat>('A4');
  const [landscape, setLandscape] = useState(false);
  const [printBackground, setPrintBackground] = useState(true);

  // Results
  const [imageResult, setImageResult] = useState<string | null>(null);
  const [previewResult, setPreviewResult] = useState<{
    title?: string;
    description?: string;
    image?: string;
    favicon?: string;
  } | null>(null);
  const [pdfResult, setPdfResult] = useState<{ base64: string; pages: number } | null>(null);

  const screenshot = useScreenshot();
  const preview = usePreview();
  const pdf = usePdf();

  const isLoading = screenshot.isPending || preview.isPending || pdf.isPending;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setImageResult(null);
    setPreviewResult(null);
    setPdfResult(null);

    try {
      if (mode === 'screenshot') {
        const result = await screenshot.mutateAsync({
          url,
          full_page: fullPage,
          format,
          quality: format !== 'png' ? quality : undefined,
          width,
          height,
          wait_seconds: waitSeconds,
          selector: selector || undefined,
        });
        if (result.success) {
          setImageResult(`data:image/${result.format};base64,${result.image_base64}`);
        }
      } else if (mode === 'preview') {
        const result = await preview.mutateAsync({
          url,
          width: 1200,
          height: 630,
        });
        if (result.success) {
          setPreviewResult({
            title: result.title,
            description: result.description,
            image: result.image_base64
              ? `data:image/png;base64,${result.image_base64}`
              : result.og_image_url,
            favicon: result.favicon_url,
          });
        }
      } else if (mode === 'pdf') {
        const result = await pdf.mutateAsync({
          url,
          format: pdfFormat,
          landscape,
          print_background: printBackground,
        });
        if (result.success) {
          setPdfResult({
            base64: result.pdf_base64,
            pages: result.pages,
          });
        }
      }
    } catch (err) {
      console.error('Operation failed:', err);
    }
  };

  const handleDownload = () => {
    if (mode === 'screenshot' && imageResult) {
      const link = document.createElement('a');
      link.href = imageResult;
      link.download = `screenshot.${format}`;
      link.click();
    } else if (mode === 'pdf' && pdfResult) {
      const link = document.createElement('a');
      link.href = `data:application/pdf;base64,${pdfResult.base64}`;
      link.download = 'page.pdf';
      link.click();
    }
  };

  return (
    <Card className={className}>
      <form onSubmit={handleSubmit} className="p-6">
        <h3 className="text-lg font-semibold mb-6">Screenshot & PDF Tool</h3>

        <div className="space-y-4">
          {/* URL Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              URL *
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              required
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mode
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMode('screenshot')}
                className={`px-4 py-2 rounded text-sm ${
                  mode === 'screenshot'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                Screenshot
              </button>
              <button
                type="button"
                onClick={() => setMode('preview')}
                className={`px-4 py-2 rounded text-sm ${
                  mode === 'preview'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                Link Preview
              </button>
              <button
                type="button"
                onClick={() => setMode('pdf')}
                className={`px-4 py-2 rounded text-sm ${
                  mode === 'pdf'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                PDF
              </button>
            </div>
          </div>

          {/* Screenshot Options */}
          {mode === 'screenshot' && (
            <>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Format
                  </label>
                  <select
                    value={format}
                    onChange={(e) => setFormat(e.target.value as ScreenshotFormat)}
                    className="w-full px-3 py-2 border rounded"
                  >
                    <option value="png">PNG</option>
                    <option value="jpeg">JPEG</option>
                    <option value="webp">WebP</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Width
                  </label>
                  <input
                    type="number"
                    value={width}
                    onChange={(e) => setWidth(parseInt(e.target.value) || 1280)}
                    min={320}
                    max={3840}
                    className="w-full px-3 py-2 border rounded"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Height
                  </label>
                  <input
                    type="number"
                    value={height}
                    onChange={(e) => setHeight(parseInt(e.target.value) || 720)}
                    min={240}
                    max={2160}
                    className="w-full px-3 py-2 border rounded"
                  />
                </div>
              </div>

              {format !== 'png' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quality: {quality}%
                  </label>
                  <input
                    type="range"
                    value={quality}
                    onChange={(e) => setQuality(parseInt(e.target.value))}
                    min={10}
                    max={100}
                    className="w-full"
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Wait (seconds)
                  </label>
                  <input
                    type="number"
                    value={waitSeconds}
                    onChange={(e) => setWaitSeconds(parseInt(e.target.value) || 2)}
                    min={0}
                    max={30}
                    className="w-full px-3 py-2 border rounded"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Element Selector (optional)
                  </label>
                  <input
                    type="text"
                    value={selector}
                    onChange={(e) => setSelector(e.target.value)}
                    placeholder="article.main"
                    className="w-full px-3 py-2 border rounded"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="fullPage"
                  checked={fullPage}
                  onChange={(e) => setFullPage(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="fullPage" className="text-sm text-gray-700">
                  Full Page Screenshot
                </label>
              </div>
            </>
          )}

          {/* PDF Options */}
          {mode === 'pdf' && (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Page Format
                  </label>
                  <select
                    value={pdfFormat}
                    onChange={(e) => setPdfFormat(e.target.value as PdfFormat)}
                    className="w-full px-3 py-2 border rounded"
                  >
                    <option value="A4">A4</option>
                    <option value="Letter">Letter</option>
                    <option value="Legal">Legal</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={landscape}
                    onChange={(e) => setLandscape(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Landscape</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={printBackground}
                    onChange={(e) => setPrintBackground(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Print Background</span>
                </label>
              </div>
            </>
          )}
        </div>

        {/* Submit */}
        <div className="mt-6">
          <button
            type="submit"
            disabled={isLoading || !url}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading
              ? 'Processing...'
              : mode === 'screenshot'
              ? 'Take Screenshot'
              : mode === 'preview'
              ? 'Generate Preview'
              : 'Generate PDF'}
          </button>
        </div>

        {/* Screenshot Result */}
        {imageResult && (
          <div className="mt-6">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium">Screenshot</h4>
              <button
                onClick={handleDownload}
                className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
              >
                Download
              </button>
            </div>
            <div className="border rounded overflow-hidden">
              <img src={imageResult} alt="Screenshot" className="w-full" />
            </div>
          </div>
        )}

        {/* Preview Result */}
        {previewResult && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-3">Link Preview</h4>
            <div className="bg-white border rounded-lg overflow-hidden">
              {previewResult.image && (
                <img
                  src={previewResult.image}
                  alt=""
                  className="w-full h-48 object-cover"
                />
              )}
              <div className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  {previewResult.favicon && (
                    <img src={previewResult.favicon} alt="" className="w-4 h-4" />
                  )}
                  <span className="text-xs text-gray-500">{url}</span>
                </div>
                {previewResult.title && (
                  <h5 className="font-medium text-lg">{previewResult.title}</h5>
                )}
                {previewResult.description && (
                  <p className="text-sm text-gray-600 mt-1">{previewResult.description}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* PDF Result */}
        {pdfResult && (
          <div className="mt-6">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium">PDF Generated ({pdfResult.pages} pages)</h4>
              <button
                onClick={handleDownload}
                className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200"
              >
                Download PDF
              </button>
            </div>
          </div>
        )}

        {/* Errors */}
        {(screenshot.error || preview.error || pdf.error) && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded text-sm">
            {(screenshot.error || preview.error || pdf.error)?.message}
          </div>
        )}
      </form>
    </Card>
  );
};
