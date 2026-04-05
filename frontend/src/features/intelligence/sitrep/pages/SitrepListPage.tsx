/**
 * SitrepListPage - List of all SITREP reports
 *
 * Features:
 * - List all SITREPs with pagination
 * - Filter by report type (daily, weekly, breaking)
 * - Filter by category (politics, finance, conflict_security, technology, crypto)
 * - Category Matrix UI showing counts for category+type combinations
 * - Generate new SITREP on demand
 * - Quick view of latest SITREP
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  FileText,
  RefreshCw,
  Clock,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Plus,
  ChevronRight,
  Calendar,
  BarChart3,
  Zap,
  Grid3X3,
} from 'lucide-react';
import { useSitreps, useGenerateSitrep, useLatestSitrep } from '../api/useSitreps';
import type { Sitrep, SitrepListParams, SitrepCategory } from '../types/sitrep.types';
import { SITREP_CATEGORY_LABELS } from '../types/sitrep.types';
import { formatDistanceToNow, format } from 'date-fns';

// =============================================================================
// Constants
// =============================================================================

const REPORT_TYPES = ['daily', 'weekly', 'breaking'] as const;

/**
 * Available SITREP categories - aligned with Tier-0 Triage Agent
 * Source: services/content-analysis-v3/app/pipeline/tier0/triage.py
 */
const CATEGORIES: SitrepCategory[] = [
  'conflict',
  'finance',
  'politics',
  'humanitarian',
  'security',
  'technology',
  'other',
  'crypto',
];

/**
 * Category badge color mappings
 */
const CATEGORY_COLORS: Record<SitrepCategory, string> = {
  conflict: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  finance: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  politics: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  humanitarian: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200',
  security: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  technology: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  other: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  crypto: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
};

// =============================================================================
// Components
// =============================================================================

interface CategoryBadgeProps {
  category: SitrepCategory;
}

function CategoryBadge({ category }: CategoryBadgeProps) {
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${CATEGORY_COLORS[category]}`}>
      {SITREP_CATEGORY_LABELS[category]}
    </span>
  );
}

interface SitrepCardProps {
  sitrep: Sitrep;
}

function SitrepCard({ sitrep }: SitrepCardProps) {
  const typeColors = {
    daily: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    weekly: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    breaking: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  };

  const typeIcons = {
    daily: Calendar,
    weekly: BarChart3,
    breaking: Zap,
  };

  const TypeIcon = typeIcons[sitrep.report_type] || FileText;

  return (
    <Link to={`/intelligence/sitrep/${sitrep.id}`}>
      <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${typeColors[sitrep.report_type]}`}>
                <TypeIcon className="h-3 w-3" />
                {sitrep.report_type}
              </span>
              {sitrep.category && (
                <CategoryBadge category={sitrep.category} />
              )}
              {sitrep.human_reviewed && (
                <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200 flex items-center gap-1">
                  <CheckCircle className="h-3 w-3" />
                  Reviewed
                </span>
              )}
            </div>
            <h3 className="font-semibold text-lg mb-1 line-clamp-1">{sitrep.title}</h3>
            <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
              {sitrep.executive_summary}
            </p>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {sitrep.created_at
                  ? formatDistanceToNow(new Date(sitrep.created_at), { addSuffix: true })
                  : format(new Date(sitrep.report_date), 'PP')}
              </span>
              <span>{sitrep.articles_analyzed} articles</span>
              <span>{Math.round(sitrep.confidence_score * 100)}% confidence</span>
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        </div>
      </Card>
    </Link>
  );
}

function LatestSitrepCard() {
  const { data: sitrep, isLoading, error } = useLatestSitrep('daily');

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </Card>
    );
  }

  if (error || !sitrep) {
    return (
      <Card className="p-6">
        <div className="text-center py-8 text-muted-foreground">
          <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No SITREP available yet</p>
          <p className="text-sm">Generate your first report below</p>
        </div>
      </Card>
    );
  }

  return (
    <Link to={`/intelligence/sitrep/${sitrep.id}`}>
      <Card className="p-6 hover:shadow-md transition-shadow cursor-pointer border-primary/20">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">Latest SITREP</h3>
          {sitrep.category && (
            <CategoryBadge category={sitrep.category} />
          )}
          <span className="text-xs text-muted-foreground ml-auto">
            {format(new Date(sitrep.created_at), 'PPp')}
          </span>
        </div>
        <h4 className="text-lg font-medium mb-2">{sitrep.title}</h4>
        <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
          {sitrep.executive_summary}
        </p>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-primary font-medium">Read full report &rarr;</span>
        </div>
      </Card>
    </Link>
  );
}

interface CategoryMatrixProps {
  sitreps: Sitrep[];
  selectedType: string | undefined;
  selectedCategory: SitrepCategory | undefined;
  onCellClick: (type: string | undefined, category: SitrepCategory | undefined) => void;
}

function CategoryMatrix({ sitreps, selectedType, selectedCategory, onCellClick }: CategoryMatrixProps) {
  // Calculate counts for each category+type combination
  const matrix = useMemo(() => {
    const counts: Record<string, Record<string, number>> = {};

    // Initialize matrix with zeros
    for (const category of CATEGORIES) {
      counts[category] = {};
      for (const type of REPORT_TYPES) {
        counts[category][type] = 0;
      }
    }

    // Count sitreps
    for (const sitrep of sitreps) {
      const cat = sitrep.category;
      const type = sitrep.report_type;
      if (cat && counts[cat]) {
        counts[cat][type] = (counts[cat][type] || 0) + 1;
      }
    }

    return counts;
  }, [sitreps]);

  // Calculate row and column totals
  const rowTotals = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const category of CATEGORIES) {
      totals[category] = REPORT_TYPES.reduce((sum, type) => sum + (matrix[category]?.[type] || 0), 0);
    }
    return totals;
  }, [matrix]);

  const colTotals = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const type of REPORT_TYPES) {
      totals[type] = CATEGORIES.reduce((sum, cat) => sum + (matrix[cat]?.[type] || 0), 0);
    }
    return totals;
  }, [matrix]);

  const grandTotal = CATEGORIES.reduce((sum, cat) => sum + rowTotals[cat], 0);

  const isSelected = (type: string | undefined, category: SitrepCategory | undefined) => {
    return selectedType === type && selectedCategory === category;
  };

  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-4">
        <Grid3X3 className="h-5 w-5 text-muted-foreground" />
        <h3 className="font-semibold">Category Matrix</h3>
        <span className="text-sm text-muted-foreground ml-auto">
          Click a cell to filter
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 px-2 font-medium text-muted-foreground">Category</th>
              {REPORT_TYPES.map(type => (
                <th key={type} className="text-center py-2 px-2 font-medium text-muted-foreground capitalize">
                  {type}
                </th>
              ))}
              <th className="text-center py-2 px-2 font-medium text-muted-foreground">Total</th>
            </tr>
          </thead>
          <tbody>
            {CATEGORIES.map(category => (
              <tr key={category} className="border-b last:border-b-0">
                <td className="py-2 px-2">
                  <button
                    onClick={() => onCellClick(undefined, selectedCategory === category ? undefined : category)}
                    className={`w-full text-left px-2 py-1 rounded transition-colors ${
                      selectedCategory === category && !selectedType
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    }`}
                  >
                    {SITREP_CATEGORY_LABELS[category]}
                  </button>
                </td>
                {REPORT_TYPES.map(type => {
                  const count = matrix[category]?.[type] || 0;
                  const cellSelected = isSelected(type, category);
                  return (
                    <td key={type} className="text-center py-2 px-2">
                      <button
                        onClick={() => onCellClick(
                          cellSelected ? undefined : type,
                          cellSelected ? undefined : category
                        )}
                        className={`w-full py-1 px-2 rounded transition-colors ${
                          cellSelected
                            ? 'bg-primary text-primary-foreground'
                            : count > 0
                              ? 'hover:bg-muted cursor-pointer'
                              : 'text-muted-foreground'
                        }`}
                        disabled={count === 0 && !cellSelected}
                      >
                        {count}
                      </button>
                    </td>
                  );
                })}
                <td className="text-center py-2 px-2 font-medium">
                  {rowTotals[category]}
                </td>
              </tr>
            ))}
            <tr className="bg-muted/50">
              <td className="py-2 px-2 font-medium">Total</td>
              {REPORT_TYPES.map(type => (
                <td key={type} className="text-center py-2 px-2 font-medium">
                  <button
                    onClick={() => onCellClick(
                      selectedType === type && !selectedCategory ? undefined : type,
                      undefined
                    )}
                    className={`w-full py-1 px-2 rounded transition-colors ${
                      selectedType === type && !selectedCategory
                        ? 'bg-primary text-primary-foreground'
                        : 'hover:bg-muted'
                    }`}
                  >
                    {colTotals[type]}
                  </button>
                </td>
              ))}
              <td className="text-center py-2 px-2 font-bold">
                <button
                  onClick={() => onCellClick(undefined, undefined)}
                  className={`w-full py-1 px-2 rounded transition-colors ${
                    !selectedType && !selectedCategory
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  }`}
                >
                  {grandTotal}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Active filter indicator */}
      {(selectedType || selectedCategory) && (
        <div className="mt-3 pt-3 border-t flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Active filter:</span>
          {selectedCategory && (
            <span className={`px-2 py-0.5 rounded ${CATEGORY_COLORS[selectedCategory]}`}>
              {SITREP_CATEGORY_LABELS[selectedCategory]}
            </span>
          )}
          {selectedType && (
            <span className="px-2 py-0.5 rounded bg-muted capitalize">
              {selectedType}
            </span>
          )}
          <button
            onClick={() => onCellClick(undefined, undefined)}
            className="ml-auto text-xs text-muted-foreground hover:text-foreground"
          >
            Clear filter
          </button>
        </div>
      )}
    </Card>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export function SitrepListPage() {
  const [params, setParams] = useState<SitrepListParams>({
    limit: 100, // Fetch more to calculate matrix counts
    offset: 0,
  });
  const [selectedType, setSelectedType] = useState<string | undefined>();
  const [selectedCategory, setSelectedCategory] = useState<SitrepCategory | undefined>();

  // Fetch all sitreps for matrix calculation (API max is 100)
  const { data: allData, isLoading: allLoading } = useSitreps({
    limit: 100,
    offset: 0,
  });

  // Fetch filtered sitreps for display
  const { data, isLoading, error, refetch } = useSitreps({
    ...params,
    report_type: selectedType as 'daily' | 'weekly' | 'breaking' | undefined,
    category: selectedCategory,
  });

  const generateMutation = useGenerateSitrep();

  const handleGenerate = async (type: 'daily' | 'weekly' | 'breaking') => {
    try {
      await generateMutation.mutateAsync({
        report_type: type,
        category: selectedCategory,
        top_stories_count: 10,
        min_cluster_size: 2,
      });
    } catch (err) {
      console.error('Failed to generate SITREP:', err);
    }
  };

  const handleMatrixCellClick = (type: string | undefined, category: SitrepCategory | undefined) => {
    setSelectedType(type);
    setSelectedCategory(category);
    setParams(p => ({ ...p, offset: 0 })); // Reset pagination on filter change
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">SITREP Reports</h1>
          <p className="text-muted-foreground">
            AI-generated intelligence briefings from news clusters
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => refetch()}
            variant="outline"
            size="sm"
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={() => handleGenerate((selectedType as 'daily' | 'weekly' | 'breaking') || 'daily')}
            disabled={generateMutation.isPending}
          >
            {generateMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Plus className="h-4 w-4 mr-2" />
            )}
            Generate SITREP
            {selectedCategory && (
              <span className="ml-1 text-xs opacity-75">
                ({SITREP_CATEGORY_LABELS[selectedCategory]})
              </span>
            )}
          </Button>
        </div>
      </div>

      {/* Latest SITREP Highlight */}
      <LatestSitrepCard />

      {/* Category Matrix */}
      {!allLoading && allData?.sitreps && (
        <CategoryMatrix
          sitreps={allData.sitreps}
          selectedType={selectedType}
          selectedCategory={selectedCategory}
          onCellClick={handleMatrixCellClick}
        />
      )}

      {/* Type Filters (legacy buttons for quick access) */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Quick filter:</span>
        {['all', 'daily', 'weekly', 'breaking'].map((type) => (
          <Button
            key={type}
            variant={selectedType === type || (type === 'all' && !selectedType) ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setSelectedType(type === 'all' ? undefined : type);
              setParams(p => ({ ...p, offset: 0 }));
            }}
          >
            {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
          </Button>
        ))}

        {/* Category dropdown or quick buttons */}
        <span className="text-sm text-muted-foreground ml-4">Category:</span>
        <Button
          variant={!selectedCategory ? 'default' : 'outline'}
          size="sm"
          onClick={() => {
            setSelectedCategory(undefined);
            setParams(p => ({ ...p, offset: 0 }));
          }}
        >
          All
        </Button>
        {CATEGORIES.map((cat) => (
          <Button
            key={cat}
            variant={selectedCategory === cat ? 'default' : 'outline'}
            size="sm"
            onClick={() => {
              setSelectedCategory(selectedCategory === cat ? undefined : cat);
              setParams(p => ({ ...p, offset: 0 }));
            }}
            className="hidden md:inline-flex"
          >
            {SITREP_CATEGORY_LABELS[cat]}
          </Button>
        ))}
      </div>

      {/* Error Display */}
      {error && (
        <Card className="p-4 bg-destructive/10 border-destructive">
          <div className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            <p>Failed to load SITREPs. Please try again.</p>
          </div>
        </Card>
      )}

      {/* Generation Status */}
      {generateMutation.isPending && (
        <Card className="p-4 bg-primary/10 border-primary">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
            <div>
              <p className="font-medium">Generating SITREP...</p>
              <p className="text-sm text-muted-foreground">
                This may take 15-30 seconds
                {selectedCategory && (
                  <span> (Category: {SITREP_CATEGORY_LABELS[selectedCategory]})</span>
                )}
              </p>
            </div>
          </div>
        </Card>
      )}

      {generateMutation.isSuccess && (
        <Card className="p-4 bg-green-100 dark:bg-green-900/20 border-green-500">
          <div className="flex items-center gap-2 text-green-800 dark:text-green-200">
            <CheckCircle className="h-5 w-5" />
            <p>SITREP generated successfully!</p>
          </div>
        </Card>
      )}

      {/* SITREP List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : data?.sitreps && data.sitreps.length > 0 ? (
        <div className="space-y-3">
          {data.sitreps.map((sitrep) => (
            <SitrepCard key={sitrep.id} sitrep={sitrep} />
          ))}

          {/* Pagination */}
          {data.has_more && (
            <div className="flex justify-center pt-4">
              <Button
                variant="outline"
                onClick={() => setParams(p => ({ ...p, offset: (p.offset || 0) + (p.limit || 20) }))}
              >
                Load More
              </Button>
            </div>
          )}
        </div>
      ) : (
        <Card className="p-12">
          <div className="text-center text-muted-foreground">
            <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No SITREPs Found</h3>
            <p className="mb-4">
              {selectedCategory || selectedType ? (
                <>No SITREPs match the current filter. Try adjusting your selection or generate a new one.</>
              ) : (
                <>Generate your first intelligence briefing to get started</>
              )}
            </p>
            <Button onClick={() => handleGenerate('daily')}>
              <Plus className="h-4 w-4 mr-2" />
              Generate First SITREP
            </Button>
          </div>
        </Card>
      )}

      {/* Stats Footer */}
      {data && (
        <div className="text-sm text-muted-foreground text-center">
          Showing {data.sitreps.length} of {data.total} reports
          {(selectedType || selectedCategory) && (
            <span className="ml-1">
              (filtered{selectedCategory && `: ${SITREP_CATEGORY_LABELS[selectedCategory]}`}
              {selectedType && `, ${selectedType}`})
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default SitrepListPage;
