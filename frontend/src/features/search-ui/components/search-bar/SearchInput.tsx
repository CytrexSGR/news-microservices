/**
 * SearchInput - Search input with autocomplete
 */

import { useState, useRef, useEffect } from 'react'
import { Search, Loader2, X } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useQuery } from '@tanstack/react-query'
import { getAutocomplete } from '@/lib/api/searchPublic'
import { cn } from '@/lib/utils'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  onSearch?: (query: string) => void
  placeholder?: string
  showSuggestions?: boolean
  className?: string
}

export function SearchInput({
  value,
  onChange,
  onSearch,
  placeholder = 'Search articles...',
  showSuggestions = true,
  className,
}: SearchInputProps) {
  const [isFocused, setIsFocused] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Fetch suggestions
  const { data: autocompleteData, isLoading } = useQuery({
    queryKey: ['autocomplete', value],
    queryFn: () => getAutocomplete(value, 10),
    enabled: value.length >= 2 && showSuggestions,
    staleTime: 2 * 60 * 1000,
  })

  const suggestions = autocompleteData?.suggestions || []
  const showDropdown = isFocused && showSuggestions && (suggestions.length > 0 || isLoading)

  // Handle click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsFocused(false)
        setSelectedIndex(-1)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown) {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleSearch()
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, suggestions.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, -1))
        break
      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && suggestions[selectedIndex]) {
          handleSelectSuggestion(suggestions[selectedIndex])
        } else {
          handleSearch()
        }
        break
      case 'Escape':
        setIsFocused(false)
        setSelectedIndex(-1)
        inputRef.current?.blur()
        break
    }
  }

  const handleSelectSuggestion = (suggestion: string) => {
    onChange(suggestion)
    setIsFocused(false)
    setSelectedIndex(-1)
    onSearch?.(suggestion)
  }

  const handleSearch = () => {
    onSearch?.(value)
    setIsFocused(false)
    setSelectedIndex(-1)
    inputRef.current?.blur()
  }

  const handleClear = () => {
    onChange('')
    inputRef.current?.focus()
  }

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground pointer-events-none" />

        <Input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          placeholder={placeholder}
          className="pl-10 pr-20"
        />

        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {isLoading && <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" />}

          {value && (
            <Button type="button" variant="ghost" size="sm" onClick={handleClear} className="h-7 w-7 p-0">
              <X className="h-4 w-4" />
            </Button>
          )}

          <Button type="button" size="sm" onClick={handleSearch} className="h-7">
            Search
          </Button>
        </div>
      </div>

      {showDropdown && (
        <div className="absolute z-50 w-full mt-1 bg-background border rounded-md shadow-lg max-h-60 overflow-y-auto">
          {isLoading && (
            <div className="px-4 py-3 text-sm text-muted-foreground text-center">Loading...</div>
          )}

          {!isLoading && suggestions.length === 0 && (
            <div className="px-4 py-3 text-sm text-muted-foreground text-center">No suggestions</div>
          )}

          {!isLoading && suggestions.length > 0 && (
            <div className="py-1">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectSuggestion(suggestion)}
                  className={cn(
                    'w-full px-4 py-2 text-left text-sm hover:bg-accent cursor-pointer transition-colors',
                    index === selectedIndex && 'bg-accent'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <span>{suggestion}</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
