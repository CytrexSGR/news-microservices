/**
 * ResearchPage
 *
 * Main research dashboard with tabs for:
 * - New Research: Create new research tasks
 * - Templates: Browse and apply templates
 * - History: View past research tasks
 * - Statistics: Usage and cost overview
 */

import { useState } from 'react';
import {
  Search,
  FileText,
  History,
  BarChart3,
  Beaker,
} from 'lucide-react';
import {
  ResearchForm,
  ResearchHistory,
  TemplateList,
  UsageStatsCard,
} from '@/features/research';

type TabId = 'new' | 'templates' | 'history' | 'stats';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
}

const TABS: Tab[] = [
  { id: 'new', label: 'New Research', icon: <Search className="h-4 w-4" /> },
  { id: 'templates', label: 'Templates', icon: <FileText className="h-4 w-4" /> },
  { id: 'history', label: 'History', icon: <History className="h-4 w-4" /> },
  { id: 'stats', label: 'Statistics', icon: <BarChart3 className="h-4 w-4" /> },
];

export function ResearchPage() {
  const [activeTab, setActiveTab] = useState<TabId>('new');
  const [selectedTaskId, setSelectedTaskId] = useState<number | undefined>();

  const handleTaskCreated = (taskId: number) => {
    setSelectedTaskId(taskId);
    setActiveTab('history');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Beaker className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-foreground">
                Research Dashboard
              </h1>
              <p className="text-sm text-muted-foreground">
                AI-powered research with Perplexity
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="flex gap-6">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'new' && (
          <div className="max-w-2xl">
            <div className="bg-card border border-border rounded-lg p-6">
              <ResearchForm onTaskCreated={handleTaskCreated} />
            </div>

            {/* Quick Stats Sidebar */}
            <div className="mt-6">
              <UsageStatsCard days={7} />
            </div>
          </div>
        )}

        {activeTab === 'templates' && (
          <TemplateList onTaskCreated={handleTaskCreated} />
        )}

        {activeTab === 'history' && (
          <ResearchHistory
            onTaskSelect={setSelectedTaskId}
            selectedTaskId={selectedTaskId}
          />
        )}

        {activeTab === 'stats' && (
          <div className="grid gap-6 md:grid-cols-2">
            <UsageStatsCard days={7} />
            <UsageStatsCard days={30} />
          </div>
        )}
      </div>
    </div>
  );
}

export default ResearchPage;
