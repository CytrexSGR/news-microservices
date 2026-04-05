/**
 * HTML utilities for cleaning and extracting text from HTML content.
 * Used across the application for displaying article previews.
 */

/**
 * Removes HTML tags from a string and returns clean text.
 * Uses multi-stage cleaning for robust HTML removal:
 * 1. DOM parsing (handles most HTML)
 * 2. Regex cleanup (removes remaining artifacts)
 * 3. Whitespace normalization
 * 4. HTML entity decoding
 *
 * Handles complex cases like:
 * - Nested HTML structures (Middle East Eye: <article><div><h2>...)
 * - Inline styles and attributes (Der Standard: <img style="...">)
 * - Mixed HTML and text content
 * - HTML entities (&nbsp;, &amp;, etc.)
 *
 * @param html - HTML string to clean
 * @returns Plain text without HTML tags, normalized whitespace
 */
export function stripHtml(html: string): string {
  if (!html) return '';

  // Stage 1: DOM parsing - handles nested structures
  const tmp = document.createElement('DIV');
  tmp.innerHTML = html;
  let text = tmp.textContent || tmp.innerText || '';

  // Stage 2: Regex cleanup - remove any remaining HTML artifacts
  // Remove any remaining tags that might have been missed
  text = text.replace(/<[^>]*>/g, '');

  // Remove HTML entities (common ones)
  text = text.replace(/&nbsp;/g, ' ');
  text = text.replace(/&amp;/g, '&');
  text = text.replace(/&lt;/g, '<');
  text = text.replace(/&gt;/g, '>');
  text = text.replace(/&quot;/g, '"');
  text = text.replace(/&#39;/g, "'");

  // Stage 3: Whitespace normalization
  // Replace multiple spaces/newlines with single space
  text = text.replace(/\s+/g, ' ');

  // Remove leading/trailing whitespace
  text = text.trim();

  return text;
}

/**
 * Extracts the first N sentences from text for preview.
 * Useful for showing article previews without displaying entire content.
 *
 * Sentence detection handles:
 * - Period (.)
 * - Exclamation mark (!)
 * - Question mark (?)
 *
 * @param text - Text to extract sentences from (HTML will be stripped)
 * @param count - Number of sentences to extract (default: 3)
 * @returns First N sentences joined together, or full text if less than N sentences
 *
 * @example
 * getFirstSentences("Hello. World! How are you?", 2)
 * // Returns: "Hello. World!"
 */
export function getFirstSentences(text: string, count: number = 3): string {
  if (!text) return '';

  // Strip HTML first
  const cleanText = stripHtml(text);

  // Split by sentence boundaries (., !, ?)
  const sentences = cleanText.match(/[^.!?]+[.!?]+/g) || [];

  // Return first N sentences or full text if less than N
  return sentences.slice(0, count).join(' ').trim();
}
