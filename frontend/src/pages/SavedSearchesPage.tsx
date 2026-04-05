/**
 * SavedSearchesPage - Manage saved searches
 *
 * Location: /search/saved
 * Access: Protected (authentication required)
 *
 * Features:
 * - List all saved searches
 * - Run, edit, delete actions
 * - Link back to search page
 */

import { useNavigate } from 'react-router-dom'
import { Bookmark, ArrowLeft, Search } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { SavedSearchesList } from '@/features/search/components'
import { useSavedSearches } from '@/features/search/api'

export function SavedSearchesPage() {
  const navigate = useNavigate()
  const { data } = useSavedSearches()

  const handleRunSearch = (results: { query: string; total: number }) => {
    // Navigate to search page with query
    if (results.query) {
      navigate(`/search?q=${encodeURIComponent(results.query)}`)
    } else {
      navigate('/search')
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Bookmark className="h-6 w-6 text-primary" />
            <h1 className="text-3xl font-bold tracking-tight">Saved Searches</h1>
          </div>
          <p className="text-muted-foreground">
            {data?.total
              ? `${data.total} saved ${data.total === 1 ? 'search' : 'searches'}`
              : 'Manage your saved search queries'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => navigate('/search')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Search
          </Button>
          <Button onClick={() => navigate('/search')}>
            <Search className="mr-2 h-4 w-4" />
            New Search
          </Button>
        </div>
      </div>

      {/* Saved Searches List */}
      <SavedSearchesList onRunSearch={handleRunSearch} />
    </div>
  )
}
