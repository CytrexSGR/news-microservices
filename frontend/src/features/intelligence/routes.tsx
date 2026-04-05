import React from 'react';
import { Route, Routes, Navigate } from 'react-router-dom';

// Analysis pages
import { AnalysisPage, EntitiesPage as AnalysisEntitiesPage } from './analysis';

// Entity Canonicalization pages
import {
  EntitiesPage,
  EntityClustersPage,
  BatchCanonPage,
  EntityDashboardPage,
  EntityDetailsPage,
} from './entities';

// OSINT pages
import {
  OsintDashboardPage,
  PatternsPage,
  QualityPage,
  TemplatesPage,
  TemplateDetailsPage,
  InstancesPage,
  CreateInstancePage,
  InstanceDetailsPage,
  ExecutionResultsPage,
  AlertsPage,
} from './osint';

// Events pages
import {
  EventsPage,
  ClusterDetailsPage,
  LatestEventsPage,
  IntelligenceDashboardPage,
  SubcategoriesPage,
  RiskHistoryPage,
} from './events';

// Narrative pages
import {
  NarrativeAnalysisPage,
  FramesPage,
  BiasPage,
  NarrativeDashboardPage,
  NarrativeClustersPage,
} from './narrative';

// SITREP pages
import { SitrepListPage, SitrepDetailPage } from './sitrep';

// Topics pages
import { TopicListPage, TopicDetailPage } from './topics';

// Burst Detection pages
import { BurstListPage } from './bursts';

/**
 * Intelligence Routes
 *
 * All routes under /intelligence/*
 * This is a CORE feature with top-level routing.
 */
export const IntelligenceRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Default redirect to dashboard */}
      <Route index element={<Navigate to="dashboard" replace />} />

      {/* Main Dashboard */}
      <Route path="dashboard" element={<IntelligenceDashboardPage />} />

      {/* Content Analysis routes */}
      <Route path="analysis" element={<AnalysisPage />} />
      <Route path="analysis/entities" element={<AnalysisEntitiesPage />} />

      {/* Entity Canonicalization routes */}
      <Route path="entities" element={<EntitiesPage />} />
      <Route path="entities/clusters" element={<EntityClustersPage />} />
      <Route path="entities/batch" element={<BatchCanonPage />} />
      <Route path="entities/dashboard" element={<EntityDashboardPage />} />
      <Route path="entities/:canonical/aliases" element={<EntityDetailsPage />} />

      {/* OSINT routes */}
      <Route path="osint" element={<OsintDashboardPage />} />
      <Route path="osint/patterns" element={<PatternsPage />} />
      <Route path="osint/quality" element={<QualityPage />} />
      <Route path="osint/templates" element={<TemplatesPage />} />
      <Route path="osint/templates/:name" element={<TemplateDetailsPage />} />
      <Route path="osint/instances" element={<InstancesPage />} />
      <Route path="osint/instances/new" element={<CreateInstancePage />} />
      <Route path="osint/instances/:id" element={<InstanceDetailsPage />} />
      <Route path="osint/executions/:id" element={<ExecutionResultsPage />} />
      <Route path="osint/alerts" element={<AlertsPage />} />

      {/* Events routes */}
      <Route path="events" element={<EventsPage />} />
      <Route path="events/clusters/:clusterId" element={<ClusterDetailsPage />} />
      <Route path="events/latest" element={<LatestEventsPage />} />
      <Route path="events/subcategories" element={<SubcategoriesPage />} />
      <Route path="events/risk" element={<RiskHistoryPage />} />

      {/* Narrative routes */}
      <Route path="narrative" element={<NarrativeDashboardPage />} />
      <Route path="narrative/analyze" element={<NarrativeAnalysisPage />} />
      <Route path="narrative/frames" element={<FramesPage />} />
      <Route path="narrative/bias" element={<BiasPage />} />
      <Route path="narrative/clusters" element={<NarrativeClustersPage />} />

      {/* SITREP routes */}
      <Route path="sitrep" element={<SitrepListPage />} />
      <Route path="sitrep/:id" element={<SitrepDetailPage />} />

      {/* Topics routes */}
      <Route path="topics" element={<TopicListPage />} />
      <Route path="topics/:id" element={<TopicDetailPage />} />

      {/* Burst Detection routes */}
      <Route path="bursts" element={<BurstListPage />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="dashboard" replace />} />
    </Routes>
  );
};

export default IntelligenceRoutes;
