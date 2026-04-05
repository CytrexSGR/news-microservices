import React from 'react';
import { Route, Routes, Navigate } from 'react-router-dom';

// Scheduler pages
import { SchedulerDashboard, JobsPage, CronJobsPage } from './scheduler';

// MediaStack pages
import { MediaStackDashboard, MediaStackSearchPage } from './mediastack';

// Scraping pages
import {
  ScrapingDashboard,
  SourceProfilesPage,
  QueueManagementPage,
  CacheManagementPage,
  ProxyManagementPage,
  ScrapingToolsPage,
  ScreenshotPage,
} from './scraping';

/**
 * Orchestration Routes
 *
 * All routes under /admin/orchestration/*
 */
export const OrchestrationRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Default redirect to scheduler */}
      <Route index element={<Navigate to="scheduler" replace />} />

      {/* Scheduler routes */}
      <Route path="scheduler" element={<SchedulerDashboard />} />
      <Route path="scheduler/jobs" element={<JobsPage />} />
      <Route path="scheduler/cron" element={<CronJobsPage />} />

      {/* MediaStack routes */}
      <Route path="mediastack" element={<MediaStackDashboard />} />
      <Route path="mediastack/search" element={<MediaStackSearchPage />} />

      {/* Scraping routes */}
      <Route path="scraping" element={<ScrapingDashboard />} />
      <Route path="scraping/sources" element={<SourceProfilesPage />} />
      <Route path="scraping/queue" element={<QueueManagementPage />} />
      <Route path="scraping/cache" element={<CacheManagementPage />} />
      <Route path="scraping/proxies" element={<ProxyManagementPage />} />
      <Route path="scraping/tools" element={<ScrapingToolsPage />} />
      <Route path="scraping/screenshot" element={<ScreenshotPage />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="scheduler" replace />} />
    </Routes>
  );
};

export default OrchestrationRoutes;
