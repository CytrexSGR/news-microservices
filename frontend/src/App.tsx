import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { MainLayout } from '@/components/layout/MainLayout'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { LoadingFallback } from '@/components/LoadingFallback'

// Lazy-loaded pages for code splitting
const LoginPage = lazy(() => import('@/pages/LoginPage').then(m => ({ default: m.LoginPage })))
const HomePage = lazy(() => import('@/pages/HomePage').then(m => ({ default: m.HomePage })))
const FeedsPage = lazy(() => import('@/pages/FeedsPage').then(m => ({ default: m.FeedsPage })))
const FeedDetailPage = lazy(() => import('@/pages/FeedDetailPage').then(m => ({ default: m.FeedDetailPage })))
const ArticleListPage = lazy(() => import('@/pages/ArticleListPage').then(m => ({ default: m.ArticleListPage })))
const ArticleDetailPageV3 = lazy(() => import('@/pages/ArticleDetailPageV3').then(m => ({ default: m.ArticleDetailPageV3 })))
const MarketOverviewPage = lazy(() => import('@/pages/MarketOverviewPage').then(m => ({ default: m.MarketOverviewPage })))
const AssetDetailPage = lazy(() => import('@/pages/market').then(m => ({ default: m.AssetDetailPage })))
const MacroIndicatorsPage = lazy(() => import('@/pages/market').then(m => ({ default: m.MacroIndicatorsPage })))
const SearchPage = lazy(() => import('@/pages/SearchPage').then(m => ({ default: m.SearchPage })))
const SavedSearchesPage = lazy(() => import('@/pages/SavedSearchesPage').then(m => ({ default: m.SavedSearchesPage })))
const KnowledgeGraphPage = lazy(() => import('@/pages/KnowledgeGraphPage').then(m => ({ default: m.KnowledgeGraphPage })))
const IntelligenceDashboardPage = lazy(() => import('@/pages/IntelligenceDashboardPage').then(m => ({ default: m.IntelligenceDashboardPage })))
const IntelligenceRoutes = lazy(() => import('@/features/intelligence/routes').then(m => ({ default: m.IntelligenceRoutes })))
const NotificationsPage = lazy(() => import('@/pages/NotificationsPage').then(m => ({ default: m.NotificationsPage })))
const ResearchPage = lazy(() => import('@/pages/ResearchPage').then(m => ({ default: m.ResearchPage })))
const GeoMapPage = lazy(() => import('@/pages/GeoMapPage').then(m => ({ default: m.GeoMapPage })))
const GlobePage = lazy(() => import("@/features/globe/pages/GlobePage").then(m => ({ default: m.GlobePage })))

// Admin pages (rarely accessed, high priority for lazy loading)
const ContentAnalysisV3AdminPage = lazy(() => import('@/pages/admin/ContentAnalysisV3AdminPage').then(m => ({ default: m.ContentAnalysisV3AdminPage })))
const FeedServiceAdminPage = lazy(() => import('@/pages/admin/FeedServiceAdminPage').then(m => ({ default: m.FeedServiceAdminPage })))
const KnowledgeGraphAdminPage = lazy(() => import('@/pages/admin/KnowledgeGraphAdminPage').then(m => ({ default: m.KnowledgeGraphAdminPage })))
const FMPServiceAdminPage = lazy(() => import('@/pages/admin/FMPServiceAdminPage').then(m => ({ default: m.FMPServiceAdminPage })))
const SearchServiceAdminPage = lazy(() => import('@/pages/admin/SearchServiceAdminPage').then(m => ({ default: m.SearchServiceAdminPage })))
const ClusteringAdminPage = lazy(() => import('@/pages/admin/ClusteringAdminPage').then(m => ({ default: m.ClusteringAdminPage })))
const OntologyProposalsPage = lazy(() => import('@/pages/admin/OntologyProposalsPage').then(m => ({ default: m.OntologyProposalsPage })))
const OntologyProposalDetailPage = lazy(() => import('@/pages/admin/OntologyProposalDetailPage').then(m => ({ default: m.OntologyProposalDetailPage })))
const HealthMonitorPage = lazy(() => import('@/pages/HealthMonitorPage').then(m => ({ default: m.HealthMonitorPage })))
// CacheMonitorPage removed - never worked, low value (2025-12-28)
const AdminDashboardPage = lazy(() => import('@/pages/admin/AdminDashboardPage').then(m => ({ default: m.AdminDashboardPage })))
// CircuitBreakerPage removed - use Grafana dashboard instead (2025-12-28)
const SchedulerAdminPage = lazy(() => import('@/pages/admin/SchedulerAdminPage').then(m => ({ default: m.SchedulerAdminPage })))
// AgentConfigurationPage removed - content-analysis-v2 service archived 2025-11-24

// Finance Terminal pages (now use MainLayout)
const PricesPage = lazy(() => import('@/features/finance/pages').then(m => ({ default: m.PricesPage })))
const MarketHoursPage = lazy(() => import('@/features/finance/pages').then(m => ({ default: m.MarketHoursPage })))
const ChartsPage = lazy(() => import('@/features/finance/pages').then(m => ({ default: m.ChartsPage })))
const HealthPage = lazy(() => import('@/features/finance/pages').then(m => ({ default: m.HealthPage })))
const FinanceSearchPage = lazy(() => import('@/features/finance/pages').then(m => ({ default: m.SearchPage })))

// Trading Terminal pages
const TradingDashboard = lazy(() => import('@/features/trading/pages').then(m => ({ default: m.TradingDashboard })))
const MarketMatrix = lazy(() => import('@/features/trading/pages').then(m => ({ default: m.MarketMatrix })))
const AnalyticsDashboard = lazy(() => import('@/features/trading/pages/AnalyticsDashboard'))
const TradingIndicatorsPage = lazy(() => import('@/features/trading/pages').then(m => ({ default: m.TradingIndicatorsPage })))
const OptimizationDashboard = lazy(() => import('@/features/trading/pages').then(m => ({ default: m.OptimizationDashboard })))
const OptimizationLab = lazy(() => import('@/features/trading/pages').then(m => ({ default: m.OptimizationLab })))
const StrategyLabLandingPage = lazy(() => import('@/features/trading/pages').then(m => ({ default: m.StrategyLabLandingPage })))
const MLLabPage = lazy(() => import('@/pages/MLLabPage'))
const StrategyEditorPage = lazy(() => import('@/features/trading/pages/StrategyEditorPage'))
const StrategyBacktestResultPage = lazy(() => import('@/features/trading/pages/StrategyBacktestResultPage'))
const StrategyDebugger = lazy(() => import('@/pages/StrategyDebugger').then(m => ({ default: m.StrategyDebugger })))
const StrategyOverview = lazy(() => import('@/pages/StrategyOverview').then(m => ({ default: m.StrategyOverview })))
const StrategyListPage = lazy(() => import('@/pages/StrategyListPage').then(m => ({ default: m.StrategyListPage })))
const DataManagementPage = lazy(() => import('@/pages/DataManagementPage').then(m => ({ default: m.DataManagementPage })))
const AgentMonitorPage = lazy(() => import('@/features/trading/pages').then(m => ({ default: m.AgentMonitorPage })))
const StrategyLabPage = lazy(() => import('@/features/trading/pages').then(m => ({ default: m.StrategyLabPage })))

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'hsl(var(--card))',
            color: 'hsl(var(--card-foreground))',
            border: '1px solid hsl(var(--border))',
          },
          success: {
            iconTheme: {
              primary: 'hsl(var(--primary))',
              secondary: 'hsl(var(--primary-foreground))',
            },
          },
          error: {
            iconTheme: {
              primary: 'hsl(var(--destructive))',
              secondary: 'hsl(var(--destructive-foreground))',
            },
          },
        }}
      />
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <HomePage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/feeds/:feedId"
          element={
            <ProtectedRoute>
              <MainLayout>
                <FeedDetailPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/feeds"
          element={
            <ProtectedRoute>
              <MainLayout>
                <FeedsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/articles"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ArticleListPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/articles/:itemId"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ArticleDetailPageV3 />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/markets"
          element={
            <ProtectedRoute>
              <MainLayout>
                <MarketOverviewPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/market/asset/:assetType/:symbol"
          element={
            <ProtectedRoute>
              <MainLayout>
                <AssetDetailPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/market/macro-indicators"
          element={
            <ProtectedRoute>
              <MainLayout>
                <MacroIndicatorsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <MainLayout>
                <SearchPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/search/saved"
          element={
            <ProtectedRoute>
              <MainLayout>
                <SavedSearchesPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/knowledge-graph"
          element={
            <ProtectedRoute>
              <MainLayout>
                <KnowledgeGraphPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/geo-map"
          element={
            <ProtectedRoute>
              <MainLayout>
                <GeoMapPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/globe"
          element={
            <ProtectedRoute>
              <MainLayout>
                <GlobePage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/intelligence"
          element={
            <ProtectedRoute>
              <MainLayout>
                <IntelligenceDashboardPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* Intelligence sub-routes (narrative, events, entities, etc.) */}
        <Route
          path="/intelligence/*"
          element={
            <ProtectedRoute>
              <MainLayout>
                <IntelligenceRoutes />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* Admin Dashboard */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <MainLayout>
                <AdminDashboardPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/services/content-analysis"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ContentAnalysisV3AdminPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/services/feed-service"
          element={
            <ProtectedRoute>
              <MainLayout>
                <FeedServiceAdminPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/services/knowledge-graph"
          element={
            <ProtectedRoute>
              <MainLayout>
                <KnowledgeGraphAdminPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/services/fmp-service"
          element={
            <ProtectedRoute>
              <MainLayout>
                <FMPServiceAdminPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/services/search-service"
          element={
            <ProtectedRoute>
              <MainLayout>
                <SearchServiceAdminPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/intelligence/clustering"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ClusteringAdminPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/ontology/proposals"
          element={
            <ProtectedRoute>
              <MainLayout>
                <OntologyProposalsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/ontology/proposals/:id"
          element={
            <ProtectedRoute>
              <MainLayout>
                <OntologyProposalDetailPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/health"
          element={
            <ProtectedRoute>
              <MainLayout>
                <HealthMonitorPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* CircuitBreakerPage removed - use Grafana dashboard instead (2025-12-28) */}
        <Route
          path="/admin/jobs"
          element={
            <ProtectedRoute>
              <MainLayout>
                <SchedulerAdminPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* AgentConfigurationPage route removed - content-analysis-v2 service archived 2025-11-24 */}
        {/* Finance Terminal - integrated into MainLayout */}
        <Route
          path="/finance"
          element={<Navigate to="/finance/prices" replace />}
        />
        <Route
          path="/finance/prices"
          element={
            <ProtectedRoute>
              <MainLayout>
                <PricesPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/finance/market-hours"
          element={
            <ProtectedRoute>
              <MainLayout>
                <MarketHoursPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/finance/charts"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ChartsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/finance/health"
          element={
            <ProtectedRoute>
              <MainLayout>
                <HealthPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/finance/search"
          element={
            <ProtectedRoute>
              <MainLayout>
                <FinanceSearchPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* Trading Terminal */}
        <Route
          path="/trading"
          element={
            <ProtectedRoute>
              <MainLayout>
                <TradingDashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/agent"
          element={
            <ProtectedRoute>
              <MainLayout>
                <AgentMonitorPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/strategy-lab"
          element={
            <ProtectedRoute>
              <MainLayout>
                <StrategyLabPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/analytics"
          element={
            <ProtectedRoute>
              <MainLayout>
                <AnalyticsDashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/matrix"
          element={
            <ProtectedRoute>
              <MainLayout>
                <MarketMatrix />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/indicators"
          element={
            <ProtectedRoute>
              <MainLayout>
                <TradingIndicatorsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/optimization"
          element={
            <ProtectedRoute>
              <OptimizationLab />
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/ml-lab"
          element={
            <ProtectedRoute>
              <MainLayout>
                <MLLabPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/backtest"
          element={
            <ProtectedRoute>
              <MainLayout>
                <StrategyLabLandingPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/backtest/strategy/:id/edit"
          element={
            <ProtectedRoute>
              <MainLayout>
                <StrategyEditorPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/backtest/results"
          element={
            <ProtectedRoute>
              <MainLayout>
                <StrategyBacktestResultPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/debug"
          element={
            <ProtectedRoute>
              <MainLayout>
                <StrategyDebugger />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/data-management"
          element={
            <ProtectedRoute>
              <MainLayout>
                <DataManagementPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/strategies"
          element={
            <ProtectedRoute>
              <MainLayout>
                <StrategyListPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/trading/strategy/:strategyId"
          element={
            <ProtectedRoute>
              <MainLayout>
                <StrategyOverview />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* Research Dashboard */}
        <Route
          path="/research"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ResearchPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* Notifications */}
        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <MainLayout>
                <NotificationsPage />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        {/* Predictions routes removed - rebuilding from scratch (2025-12-19) */}
        <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
