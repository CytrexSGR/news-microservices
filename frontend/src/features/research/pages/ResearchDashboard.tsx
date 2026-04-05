/**
 * ResearchDashboard Page
 *
 * Main research dashboard with:
 * - Research form for new queries
 * - Recent research tasks
 * - Quick stats overview
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  History,
  TrendingUp,
  ArrowRight,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { ResearchForm } from '../components/ResearchForm';
import { ResearchResultCard } from '../components/ResearchResultCard';
import { UsageStatsCard } from '../components/UsageStatsCard';
import { useResearchHistory } from '../api';

export function ResearchDashboard() {
  const navigate = useNavigate();
  const [selectedTaskId, setSelectedTaskId] = useState<number | undefined>();

  // Get recent tasks
  const { data: recentData, isLoading: recentLoading } = useResearchHistory({
    days: 7,
    page: 1,
    page_size: 5,
  });

  const handleTaskCreated = (taskId: number) => {
    setSelectedTaskId(taskId);
  };

  const handleViewResult = (taskId: number) => {
    navigate(`/research/${taskId}`);
  };

  return (
    <div className="space-y-8">
      {/* Research Form Section */}
      <section>
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Search className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-medium text-foreground">New Research</h2>
            <p className="text-sm text-muted-foreground">
              Start a new research query with Perplexity AI
            </p>
          </div>
        </div>

        <div className="max-w-2xl">
          <div className="bg-card border border-border rounded-lg p-6">
            <ResearchForm onTaskCreated={handleTaskCreated} />
          </div>
        </div>
      </section>

      {/* Two Column Layout */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* Recent Research */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <History className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-medium text-foreground">
                Recent Research
              </h2>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/research/history')}
              className="gap-1"
            >
              View all
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-3">
            {recentLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading...
              </div>
            ) : !recentData?.tasks || recentData.tasks.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground border border-dashed border-border rounded-lg">
                <p>No recent research</p>
                <p className="text-sm">Start a new research above</p>
              </div>
            ) : (
              recentData.tasks.map((task) => (
                <ResearchResultCard
                  key={task.id}
                  task={task}
                  onSelect={handleViewResult}
                  isSelected={selectedTaskId === task.id}
                />
              ))
            )}
          </div>
        </section>

        {/* Quick Stats */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-medium text-foreground">
              Usage Overview
            </h2>
          </div>

          <UsageStatsCard days={7} />
        </section>
      </div>
    </div>
  );
}
