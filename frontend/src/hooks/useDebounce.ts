import { useEffect, useState } from 'react'

/**
 * Debounce a value with a delay
 *
 * Returns the debounced value after the specified delay.
 * Useful for search inputs to reduce API calls.
 *
 * @param value - Value to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns Debounced value
 *
 * @example
 * ```tsx
 * const [query, setQuery] = useState('')
 * const debouncedQuery = useDebounce(query, 300)
 *
 * useEffect(() => {
 *   if (debouncedQuery) {
 *     // Make API call
 *   }
 * }, [debouncedQuery])
 * ```
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    // Set up timeout to update debounced value
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    // Clean up timeout on value or delay change
    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}
