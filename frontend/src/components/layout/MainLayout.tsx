import { LogOut, BarChart3, Menu, Home, Rss, Settings, Newspaper, Network, TrendingUp, LineChart, Search, Activity, FileCheck, Globe, Globe2, Clock, DollarSign, Bug, Database, Brain, Layers, Beaker, Bell, Zap, Eye, Server, MessageSquare, FileText, Tag, FlaskConical } from 'lucide-react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/Button'
import { ThemeToggle } from '@/components/ui/ThemeToggle'
import { NotificationBell } from '@/features/notifications'
import { useState } from 'react'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout, user } = useAuthStore()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Core navigation - essential daily-use features
  const navItems = [
    { path: '/', label: 'Overview', icon: Home },
    { path: '/articles', label: 'Articles', icon: Newspaper },
    { path: '/search', label: 'Search', icon: Search },
    { path: '/research', label: 'Research', icon: Beaker },
    { path: '/knowledge-graph', label: 'Knowledge Graph', icon: Network },
    { path: '/geo-map', label: 'News Map', icon: Globe },
    { path: '/globe', label: 'OSINT Globe', icon: Globe2 },
  ]

  // Intelligence & OSINT - core platform differentiator
  const intelligenceItems = [
    { path: '/intelligence', label: 'Intelligence Dashboard', icon: Eye },
    { path: '/intelligence/narrative', label: 'Narrative Analysis', icon: MessageSquare },
    { path: '/intelligence/sitrep', label: 'SITREP Reports', icon: FileText },
    { path: '/intelligence/topics', label: 'Topic Browser', icon: Tag },
    { path: '/intelligence/bursts', label: 'Burst Detection', icon: Zap },
    { path: '/notifications', label: 'Notification Center', icon: Bell },
  ]

  // Markets & Finance - combined section
  const marketItems = [
    { path: '/markets', label: 'Market Overview', icon: LineChart },
    { path: '/finance/prices', label: 'Live Prices', icon: DollarSign },
    { path: '/finance/charts', label: 'Charts', icon: BarChart3 },
    { path: '/finance/market-hours', label: 'Market Hours', icon: Clock },
    { path: '/finance/search', label: 'Symbol Search', icon: Search },
  ]

  // Trading - streamlined for daily use
  const tradingItems = [
    { path: '/trading/agent', label: 'Agent Monitor', icon: Eye },
    { path: '/trading/strategy-lab', label: 'Strategy Lab (Agent)', icon: FlaskConical },
    { path: '/trading', label: 'Trading Terminal', icon: TrendingUp },
    { path: '/trading/strategies', label: 'Strategies', icon: Layers },
    { path: '/trading/backtest', label: 'Strategy Lab', icon: BarChart3 },
    { path: '/trading/ml-lab', label: 'ML Lab', icon: Brain },
    { path: '/trading/data-management', label: 'Data Management', icon: Database },
  ]

  // Trading Tools - advanced features
  const tradingToolsItems = [
    { path: '/trading/indicators', label: 'Technical Indicators', icon: Zap },
    { path: '/trading/matrix', label: 'Market Matrix', icon: Activity },
    { path: '/trading/debug', label: 'Strategy Debugger', icon: Bug },
  ]

  // Admin - System Management
  // CircuitBreakersPage removed - use Grafana dashboard instead (2025-12-28)
  const adminItems = [
    { path: '/admin', label: 'Admin Dashboard', icon: BarChart3 },
    { path: '/admin/jobs', label: 'Scheduler / Jobs', icon: Clock },
  ]

  // Admin - Service Management
  const adminServiceItems = [
    { path: '/admin/services/feed-service', label: 'Feed Service', icon: Rss },
    { path: '/admin/services/content-analysis', label: 'Content Analysis', icon: Settings },
    { path: '/admin/services/knowledge-graph', label: 'Knowledge Graph', icon: Network },
    { path: '/admin/services/search-service', label: 'Search Service', icon: Search },
    { path: '/admin/services/fmp-service', label: 'FMP Service', icon: TrendingUp },
    { path: '/finance/health', label: 'FMP Health', icon: Server },
  ]

  // Admin - Advanced
  const adminAdvancedItems = [
    { path: '/admin/intelligence/clustering', label: 'Event Clustering', icon: Network },
    { path: '/admin/ontology/proposals', label: 'Ontology Proposals', icon: FileCheck },
  ]

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Skip to main content link for keyboard navigation */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:shadow-lg"
      >
        Skip to main content
      </a>

      {/* Sidebar */}
      <aside
        aria-label="Main navigation"
        className={`${
          sidebarOpen ? 'w-64' : 'w-16'
        } border-r border-border bg-card transition-all duration-300`}
      >
        <div className="flex h-16 items-center justify-between border-b border-border px-4">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <BarChart3 className="h-6 w-6 text-primary" />
              <span className="font-semibold text-foreground">Analytics</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            aria-label={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <Menu className="h-5 w-5" />
          </Button>
        </div>

        <nav aria-label="Primary navigation" className="p-4 space-y-6">
          {sidebarOpen ? (
            <>
              <div className="space-y-2">
                <div className="text-sm text-muted-foreground mb-2">Navigation</div>
                {navItems.map((item) => {
                const Icon = item.icon
                const isActive = isActivePath(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    aria-current={isActive ? 'page' : undefined}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                )
              })}
              </div>

              <div className="space-y-2">
                <div className="text-sm text-muted-foreground mb-2">Intelligence</div>
                {intelligenceItems.map((item) => {
                  const Icon = item.icon
                  const isActive = isActivePath(item.path)
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      aria-current={isActive ? 'page' : undefined}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>

              <div className="space-y-2">
                <div className="text-sm text-muted-foreground mb-2">Markets & Finance</div>
                {marketItems.map((item) => {
                  const Icon = item.icon
                  const isActive = isActivePath(item.path)
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      aria-current={isActive ? 'page' : undefined}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>

              <div className="space-y-2">
                <div className="text-sm text-muted-foreground mb-2">Trading</div>
                {tradingItems.map((item) => {
                  const Icon = item.icon
                  const isActive = isActivePath(item.path)
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      aria-current={isActive ? 'page' : undefined}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>

              <div className="space-y-2">
                <div className="text-sm text-muted-foreground mb-2">Trading Tools</div>
                {tradingToolsItems.map((item) => {
                  const Icon = item.icon
                  const isActive = isActivePath(item.path)
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      aria-current={isActive ? 'page' : undefined}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>

              <div className="space-y-2">
                <div className="text-sm text-muted-foreground mb-2">Admin</div>
                {adminItems.map((item) => {
                  const Icon = item.icon
                  const isActive = isActivePath(item.path)
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      aria-current={isActive ? 'page' : undefined}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>

              <div className="space-y-2">
                <div className="text-sm text-muted-foreground mb-2">Services</div>
                {adminServiceItems.map((item) => {
                  const Icon = item.icon
                  const isActive = isActivePath(item.path)
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      aria-current={isActive ? 'page' : undefined}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>

              <div className="space-y-2">
                <div className="text-sm text-muted-foreground mb-2">Advanced</div>
                {adminAdvancedItems.map((item) => {
                  const Icon = item.icon
                  const isActive = isActivePath(item.path)
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      aria-current={isActive ? 'page' : undefined}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = isActivePath(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center justify-center rounded-lg p-2 transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                    aria-label={item.label}
                    aria-current={isActive ? 'page' : undefined}
                    title={item.label}
                  >
                    <Icon className="h-5 w-5" />
                  </Link>
                )
              })}
              {intelligenceItems.map((item) => {
                const Icon = item.icon
                const isActive = isActivePath(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center justify-center rounded-lg p-2 transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                    aria-label={item.label}
                    aria-current={isActive ? 'page' : undefined}
                    title={item.label}
                  >
                    <Icon className="h-5 w-5" />
                  </Link>
                )
              })}
              {marketItems.map((item) => {
                const Icon = item.icon
                const isActive = isActivePath(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center justify-center rounded-lg p-2 transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                    aria-label={item.label}
                    aria-current={isActive ? 'page' : undefined}
                    title={item.label}
                  >
                    <Icon className="h-5 w-5" />
                  </Link>
                )
              })}
              {tradingItems.map((item) => {
                const Icon = item.icon
                const isActive = isActivePath(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center justify-center rounded-lg p-2 transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                    aria-label={item.label}
                    aria-current={isActive ? 'page' : undefined}
                    title={item.label}
                  >
                    <Icon className="h-5 w-5" />
                  </Link>
                )
              })}
              {tradingToolsItems.map((item) => {
                const Icon = item.icon
                const isActive = isActivePath(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center justify-center rounded-lg p-2 transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                    aria-label={item.label}
                    aria-current={isActive ? 'page' : undefined}
                    title={item.label}
                  >
                    <Icon className="h-5 w-5" />
                  </Link>
                )
              })}
              {adminItems.map((item) => {
                const Icon = item.icon
                const isActive = isActivePath(item.path)
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center justify-center rounded-lg p-2 transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                    aria-label={item.label}
                    aria-current={isActive ? 'page' : undefined}
                    title={item.label}
                  >
                    <Icon className="h-5 w-5" />
                  </Link>
                )
              })}
            </div>
          )}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header aria-label="Page header" className="flex h-16 items-center justify-between border-b border-border bg-card px-6">
          <div>
            <h1 className="text-xl font-semibold text-foreground">Dashboard</h1>
          </div>

          <div className="flex items-center gap-4">
            {user && (
              <div className="text-sm text-muted-foreground">
                {user.full_name || user.username}
              </div>
            )}
            <NotificationBell />
            <ThemeToggle />
            <Button variant="ghost" size="icon" onClick={handleLogout}>
              <LogOut className="h-5 w-5" />
              <span className="sr-only">Logout</span>
            </Button>
          </div>
        </header>

        {/* Page Content */}
        <main id="main-content" className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  )
}
