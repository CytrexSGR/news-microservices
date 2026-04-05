/**
 * StrategyListPage
 *
 * Displays all available trading strategies in a grid layout.
 * Provides quick access to strategy details, debug mode, and management actions.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/Dialog';
import { Label } from '@/components/ui/Label';
import { Activity, Plus, Search, Loader2, LayoutGrid, List } from 'lucide-react';
import toast from 'react-hot-toast';

import {
  useStrategyList,
  useCloneStrategy,
  useDeleteStrategy,
  StrategyCard,
} from '@/features/strategy';
import type { Strategy } from '@/features/strategy';

export const StrategyListPage: React.FC = () => {
  const navigate = useNavigate();

  // Data hooks
  const { strategies, total, isLoading, error, refetch } = useStrategyList();
  const cloneMutation = useCloneStrategy();
  const deleteMutation = useDeleteStrategy();

  // UI state
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Clone dialog state
  const [cloneDialogOpen, setCloneDialogOpen] = useState(false);
  const [strategyToClone, setStrategyToClone] = useState<Strategy | null>(null);
  const [cloneName, setCloneName] = useState('');

  // Delete dialog state
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [strategyToDelete, setStrategyToDelete] = useState<Strategy | null>(null);

  // Filter strategies based on search
  const filteredStrategies = strategies.filter((s) => {
    const name = s.definition?.name || s.name || '';
    const description = s.definition?.description || s.description || '';
    const query = searchQuery.toLowerCase();
    return name.toLowerCase().includes(query) || description.toLowerCase().includes(query);
  });

  // Clone handlers
  const handleCloneClick = (strategy: Strategy) => {
    setStrategyToClone(strategy);
    setCloneName(`${strategy.definition?.name || strategy.name || 'Strategy'} (Copy)`);
    setCloneDialogOpen(true);
  };

  const handleCloneConfirm = async () => {
    if (!strategyToClone || !cloneName.trim()) return;

    try {
      await cloneMutation.mutateAsync({
        strategyId: strategyToClone.id,
        newName: cloneName.trim(),
      });
      toast.success('Strategy cloned successfully');
      setCloneDialogOpen(false);
      setStrategyToClone(null);
      refetch();
    } catch (err) {
      toast.error(`Failed to clone strategy: ${(err as Error).message}`);
    }
  };

  // Delete handlers
  const handleDeleteClick = (strategy: Strategy) => {
    setStrategyToDelete(strategy);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!strategyToDelete) return;

    try {
      await deleteMutation.mutateAsync(strategyToDelete.id);
      toast.success('Strategy deleted successfully');
      setDeleteDialogOpen(false);
      setStrategyToDelete(null);
      refetch();
    } catch (err) {
      toast.error(`Failed to delete strategy: ${(err as Error).message}`);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Activity className="h-6 w-6" />
            Trading Strategies
          </h1>
          <p className="text-muted-foreground mt-1">
            {total} {total === 1 ? 'strategy' : 'strategies'} available
          </p>
        </div>

        <Button onClick={() => navigate('/trading/strategy-lab')}>
          <Plus className="mr-2 h-4 w-4" />
          New Strategy
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search strategies..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* View Toggle */}
        <div className="flex items-center border rounded-md">
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="sm"
            className="rounded-r-none"
            onClick={() => setViewMode('grid')}
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'secondary' : 'ghost'}
            size="sm"
            className="rounded-l-none"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Strategy Grid/List */}
      {filteredStrategies.length === 0 ? (
        <div className="text-center py-12">
          <Activity className="h-12 w-12 mx-auto text-muted-foreground opacity-50" />
          <h3 className="mt-4 text-lg font-medium">No strategies found</h3>
          <p className="text-muted-foreground mt-2">
            {searchQuery
              ? 'Try adjusting your search query'
              : 'Create your first strategy to get started'}
          </p>
          {!searchQuery && (
            <Button className="mt-4" onClick={() => navigate('/trading/strategy-lab')}>
              <Plus className="mr-2 h-4 w-4" />
              Create Strategy
            </Button>
          )}
        </div>
      ) : (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
              : 'space-y-3'
          }
        >
          {filteredStrategies.map((strategy) => (
            <StrategyCard
              key={strategy.id}
              strategy={strategy}
              onClone={handleCloneClick}
              onDelete={handleDeleteClick}
              isDeleting={deleteMutation.isPending && strategyToDelete?.id === strategy.id}
            />
          ))}
        </div>
      )}

      {/* Clone Dialog */}
      <Dialog open={cloneDialogOpen} onOpenChange={setCloneDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Clone Strategy</DialogTitle>
            <DialogDescription>
              Create a copy of "{strategyToClone?.definition?.name || strategyToClone?.name}"
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="clone-name">New Strategy Name</Label>
            <Input
              id="clone-name"
              value={cloneName}
              onChange={(e) => setCloneName(e.target.value)}
              placeholder="Enter name for the cloned strategy"
              className="mt-2"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCloneDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCloneConfirm}
              disabled={!cloneName.trim() || cloneMutation.isPending}
            >
              {cloneMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Clone Strategy
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Strategy</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "
              {strategyToDelete?.definition?.name || strategyToDelete?.name}"? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete Strategy
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
