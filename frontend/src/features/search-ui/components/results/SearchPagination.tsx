/**
 * Search Pagination Component
 *
 * Handles pagination for search results with:
 * - Page number display
 * - Previous/Next navigation
 * - Jump to page input
 * - Results per page selector
 * - Total results count
 */

import * as React from 'react'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Label } from '@/components/ui/Label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/Select'
import { cn } from '@/lib/utils'

interface SearchPaginationProps {
  /** Current page number (1-based) */
  currentPage: number
  /** Total number of pages */
  totalPages: number
  /** Results per page */
  pageSize: number
  /** Total number of results */
  totalResults: number
  /** Callback when page changes */
  onPageChange: (page: number) => void
  /** Callback when page size changes */
  onPageSizeChange: (pageSize: number) => void
  /** Loading state */
  isLoading?: boolean
  /** Custom class name */
  className?: string
}

const PAGE_SIZE_OPTIONS = [20, 50, 100] as const

/**
 * Calculate page range to display
 */
function getPageRange(currentPage: number, totalPages: number, maxVisible: number = 5): number[] {
  if (totalPages <= maxVisible) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }

  const half = Math.floor(maxVisible / 2)
  let start = Math.max(1, currentPage - half)
  const end = Math.min(totalPages, start + maxVisible - 1)

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }

  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
}

export function SearchPagination({
  currentPage,
  totalPages,
  pageSize,
  totalResults,
  onPageChange,
  onPageSizeChange,
  isLoading = false,
  className,
}: SearchPaginationProps) {
  const [jumpToPage, setJumpToPage] = React.useState('')

  // Calculate result range
  const startResult = Math.min((currentPage - 1) * pageSize + 1, totalResults)
  const endResult = Math.min(currentPage * pageSize, totalResults)

  // Page range for display
  const pageRange = getPageRange(currentPage, totalPages)

  const handlePageSizeChange = (value: string) => {
    const newPageSize = parseInt(value, 10)
    onPageSizeChange(newPageSize)
  }

  const handleJumpToPage = (e: React.FormEvent) => {
    e.preventDefault()
    const page = parseInt(jumpToPage, 10)

    if (!isNaN(page) && page >= 1 && page <= totalPages) {
      onPageChange(page)
      setJumpToPage('')
    }
  }

  const handlePrevPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1)
    }
  }

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1)
    }
  }

  const handleFirstPage = () => {
    onPageChange(1)
  }

  const handleLastPage = () => {
    onPageChange(totalPages)
  }

  // Don't render if no results
  if (totalResults === 0) {
    return null
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Results Info */}
        <div className="text-sm text-muted-foreground">
          Showing{' '}
          <span className="font-medium text-foreground">
            {startResult.toLocaleString()}
          </span>
          {' - '}
          <span className="font-medium text-foreground">
            {endResult.toLocaleString()}
          </span>
          {' of '}
          <span className="font-medium text-foreground">
            {totalResults.toLocaleString()}
          </span>
          {' results'}
        </div>

        {/* Page Size Selector */}
        <div className="flex items-center gap-2">
          <Label htmlFor="page-size" className="text-sm whitespace-nowrap">
            Per page:
          </Label>
          <Select
            value={pageSize.toString()}
            onValueChange={handlePageSizeChange}
            disabled={isLoading}
          >
            <SelectTrigger id="page-size" className="w-20">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {PAGE_SIZE_OPTIONS.map((size) => (
                <SelectItem key={size} value={size.toString()}>
                  {size}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mt-4 pt-4 border-t border-border">
          {/* Page Navigation */}
          <div className="flex items-center gap-1">
            {/* First Page */}
            <Button
              variant="outline"
              size="icon"
              onClick={handleFirstPage}
              disabled={currentPage === 1 || isLoading}
              className="h-9 w-9"
              title="First page"
            >
              <ChevronsLeft className="h-4 w-4" />
              <span className="sr-only">First page</span>
            </Button>

            {/* Previous Page */}
            <Button
              variant="outline"
              size="icon"
              onClick={handlePrevPage}
              disabled={currentPage === 1 || isLoading}
              className="h-9 w-9"
              title="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="sr-only">Previous page</span>
            </Button>

            {/* Page Numbers */}
            <div className="flex items-center gap-1">
              {pageRange.map((page) => (
                <Button
                  key={page}
                  variant={page === currentPage ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => onPageChange(page)}
                  disabled={isLoading}
                  className="h-9 w-9"
                  aria-current={page === currentPage ? 'page' : undefined}
                >
                  {page}
                </Button>
              ))}
            </div>

            {/* Next Page */}
            <Button
              variant="outline"
              size="icon"
              onClick={handleNextPage}
              disabled={currentPage === totalPages || isLoading}
              className="h-9 w-9"
              title="Next page"
            >
              <ChevronRight className="h-4 w-4" />
              <span className="sr-only">Next page</span>
            </Button>

            {/* Last Page */}
            <Button
              variant="outline"
              size="icon"
              onClick={handleLastPage}
              disabled={currentPage === totalPages || isLoading}
              className="h-9 w-9"
              title="Last page"
            >
              <ChevronsRight className="h-4 w-4" />
              <span className="sr-only">Last page</span>
            </Button>
          </div>

          {/* Jump to Page */}
          <form onSubmit={handleJumpToPage} className="flex items-center gap-2">
            <Label htmlFor="jump-to-page" className="text-sm whitespace-nowrap">
              Go to page:
            </Label>
            <Input
              id="jump-to-page"
              type="number"
              min={1}
              max={totalPages}
              value={jumpToPage}
              onChange={(e) => setJumpToPage(e.target.value)}
              placeholder={currentPage.toString()}
              disabled={isLoading}
              className="w-20 h-9"
            />
            <Button
              type="submit"
              variant="outline"
              size="sm"
              disabled={!jumpToPage || isLoading}
              className="h-9"
            >
              Go
            </Button>
          </form>
        </div>
      )}

      {/* Mobile Simplified Pagination */}
      {totalPages > 1 && (
        <div className="flex sm:hidden items-center justify-between mt-4 pt-4 border-t border-border">
          <Button
            variant="outline"
            onClick={handlePrevPage}
            disabled={currentPage === 1 || isLoading}
            className="gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>

          <span className="text-sm text-muted-foreground">
            Page {currentPage} of {totalPages}
          </span>

          <Button
            variant="outline"
            onClick={handleNextPage}
            disabled={currentPage === totalPages || isLoading}
            className="gap-2"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}

/**
 * Compact pagination variant for minimal space
 */
export function SearchPaginationCompact({
  currentPage,
  totalPages,
  onPageChange,
  isLoading = false,
  className,
}: Pick<
  SearchPaginationProps,
  'currentPage' | 'totalPages' | 'onPageChange' | 'isLoading' | 'className'
>) {
  const handlePrevPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1)
    }
  }

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1)
    }
  }

  if (totalPages <= 1) {
    return null
  }

  return (
    <div className={cn('flex items-center justify-between', className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={handlePrevPage}
        disabled={currentPage === 1 || isLoading}
        className="gap-2"
      >
        <ChevronLeft className="h-4 w-4" />
        Previous
      </Button>

      <span className="text-sm text-muted-foreground">
        Page {currentPage} of {totalPages}
      </span>

      <Button
        variant="outline"
        size="sm"
        onClick={handleNextPage}
        disabled={currentPage === totalPages || isLoading}
        className="gap-2"
      >
        Next
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}
