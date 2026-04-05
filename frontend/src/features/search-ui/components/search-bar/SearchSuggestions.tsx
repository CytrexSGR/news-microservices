import { cn } from '@/lib/utils'

export interface SearchSuggestionsProps {
  /** Array of suggestion strings */
  suggestions: string[]
  /** Currently highlighted suggestion index (-1 for none) */
  highlightedIndex: number
  /** Search query for highlighting */
  query: string
  /** Called when suggestion is clicked */
  onSelect: (suggestion: string) => void
  /** Called when mouse enters a suggestion */
  onMouseEnter: (index: number) => void
  /** Whether to show the dropdown */
  show: boolean
}

/**
 * Autocomplete suggestions dropdown component
 *
 * Features:
 * - Highlights matching text
 * - Keyboard accessible (controlled by parent)
 * - Click to select
 * - Hover to highlight
 * - Empty state message
 *
 * @example
 * ```tsx
 * <SearchSuggestions
 *   suggestions={['artificial intelligence', 'AI news']}
 *   highlightedIndex={0}
 *   query="artif"
 *   onSelect={(s) => setQuery(s)}
 *   onMouseEnter={(i) => setHighlightedIndex(i)}
 *   show={true}
 * />
 * ```
 */
export function SearchSuggestions({
  suggestions,
  highlightedIndex,
  query,
  onSelect,
  onMouseEnter,
  show,
}: SearchSuggestionsProps) {
  if (!show || suggestions.length === 0) {
    return null
  }

  /**
   * Highlight matching text in suggestion
   */
  const highlightMatch = (suggestion: string, searchQuery: string) => {
    if (!searchQuery) return suggestion

    const regex = new RegExp(`(${searchQuery})`, 'gi')
    const parts = suggestion.split(regex)

    return (
      <span>
        {parts.map((part, i) =>
          regex.test(part) ? (
            <strong key={i} className="font-semibold text-primary">
              {part}
            </strong>
          ) : (
            <span key={i}>{part}</span>
          )
        )}
      </span>
    )
  }

  return (
    <div
      className="absolute top-full left-0 right-0 z-50 mt-1 max-h-96 overflow-auto rounded-md border border-input bg-popover text-popover-foreground shadow-md"
      role="listbox"
    >
      {suggestions.map((suggestion, index) => (
        <div
          key={index}
          role="option"
          aria-selected={index === highlightedIndex}
          className={cn(
            'cursor-pointer px-4 py-2 text-sm transition-colors',
            index === highlightedIndex
              ? 'bg-accent text-accent-foreground'
              : 'hover:bg-accent/50'
          )}
          onClick={() => onSelect(suggestion)}
          onMouseEnter={() => onMouseEnter(index)}
        >
          {highlightMatch(suggestion, query)}
        </div>
      ))}
    </div>
  )
}
