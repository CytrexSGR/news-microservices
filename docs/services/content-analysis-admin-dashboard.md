# Content Analysis Admin Dashboard

## Übersicht

Umfassendes Admin-Dashboard für den content-analysis-service mit Live-Monitoring, Analyse-Ergebnissen und Konfigurationsverwaltung.

**Route:** `/admin/services/content-analysis`

**Status:** ✅ Backend komplett | ⚠️ Frontend Grundgerüst erstellt

## Implementierte Features

### Backend (✅ Komplett)

#### 1. Schemas (`app/schemas/admin.py`)
Alle Pydantic models für API requests/responses:
- `OperationsStatus` - Live operations data
- `RecentActivityResponse` - Analysis history
- `OSINTReviewSummary` - OSINT queue overview
- `ModelConfiguration` - LLM model config
- `FlushCacheResponse` - Cache flush result
- `ConfigUpdateResponse` - Config update result

#### 2. Admin Service (`app/services/admin_service.py`)
Business logic für alle Admin-Operationen:
- `get_operations_status()` - Dependencies, RabbitMQ, Performance, Cost, Cache
- `get_recent_activity()` - Last 50 analyses with filtering
- `get_osint_review_summary()` - OSINT queue stats
- `get_model_configuration()` - Current LLM settings
- `update_model_configuration()` - Runtime config updates
- `flush_cache()` - Clear Redis cache

#### 3. Cache Service erweitert (`app/services/cache_service.py`)
- `get_stats()` - Enhanced with `size_mb` field
- `flush_all()` - Returns count of flushed keys

#### 4. Internal API Endpunkte (`app/api/internal.py`)

**Live Operations:**
```
GET /api/v1/internal/status/operations
```
Returns: Dependencies health, RabbitMQ metrics, performance, cost, cache stats

**Analysis Explorer:**
```
GET /api/v1/internal/analysis/recent-activity?limit=50&failed_only=false
```
Returns: Recent analysis jobs with status, costs, errors

```
GET /api/v1/internal/osint/review-summary
```
Returns: OSINT queue count, recent events, severity breakdown

**Configuration:**
```
GET /api/v1/internal/configuration/models
PUT /api/v1/internal/configuration/models
```
Manage LLM model configuration (provider, models, overrides)

```
GET /api/v1/internal/configuration/controls
PUT /api/v1/internal/configuration/controls
```
Manage service controls (cost limits, rate limits, cache, consumer)

**Actions:**
```
POST /api/v1/internal/actions/flush-cache
```
Flush Redis cache (with confirmation)

### Frontend (⚠️ Grundgerüst erstellt)

#### Komplett implementiert:

1. **TypeScript Types** (`src/types/contentAnalysis.ts`)
   - Alle Interfaces für API responses
   - Enums für Status-Werte
   - Complete type safety

2. **API Client** (`src/lib/api/contentAnalysisAdmin.ts`)
   - Axios client mit service authentication
   - Alle API-Funktionen implementiert
   - Ready to use with React Query

3. **Shadcn/UI Komponenten**
   - ✅ Badge (`@/components/ui/badge.tsx`)
   - ✅ Progress (`@/components/ui/progress.tsx`)
   - ✅ AlertDialog (`@/components/ui/alert-dialog.tsx`)

4. **Routing & Navigation**
   - ✅ Route `/admin/services/content-analysis` in `App.tsx`
   - ✅ Admin-Sektion in `MainLayout.tsx` Navigation
   - ✅ Hauptseite `ContentAnalysisAdminPage.tsx` mit Tab-Struktur

#### Noch zu implementieren:

Die Hauptseite hat bereits die Tab-Struktur, aber die einzelnen Tab-Inhalte müssen noch erstellt werden:

**Live Operations Tab:**
- `CoreDependenciesCard.tsx` - Database, Redis, RabbitMQ, LLM Status (mit Badge)
- `EventProcessingCard.tsx` - Consumer status, queue depth, throughput, DLQ (rot wenn > 0)
- `PerformanceCostCard.tsx` - In-flight, latency, daily cost (mit Progress bar)
- `CachePerformanceCard.tsx` - Hit rate Ringdiagramm, absolute stats

**Analysis Explorer Tab:**
- `OSINTReviewSection.tsx` - Queue count, event preview
- `RecentActivityTable.tsx` - DataTable mit 50 letzten Analysen
- `FailedAnalysisDetails.tsx` - Error message expandable

**Configuration & Controls Tab:**
- `LLMModelManagement.tsx` - Provider dropdowns, analysis overrides table
- `ServiceControls.tsx` - Cache flush button (mit AlertDialog), cost/rate limits

## Nächste Schritte

### 1. React Query Hooks erstellen

`src/features/admin/content-analysis/hooks/useOperationsStatus.ts`:
```typescript
import { useQuery } from '@tanstack/react-query'
import { getOperationsStatus } from '@/lib/api/contentAnalysisAdmin'

export function useOperationsStatus(refetchInterval: number = 10000) {
  return useQuery({
    queryKey: ['content-analysis', 'operations-status'],
    queryFn: getOperationsStatus,
    refetchInterval, // Auto-refresh every 10 seconds
  })
}
```

Ähnlich für:
- `useRecentActivity.ts`
- `useOSINTReviewSummary.ts`
- `useModelConfiguration.ts` (mit useMutation für updates)

### 2. Live Operations Komponenten

**CoreDependenciesCard.tsx:**
```typescript
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/badge'
import { useOperationsStatus } from '../hooks/useOperationsStatus'

export function CoreDependenciesCard() {
  const { data } = useOperationsStatus()

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Core Dependencies</h3>
      <div className="space-y-3">
        {data?.dependencies.map((dep) => (
          <div key={dep.name} className="flex justify-between items-center">
            <span>{dep.name}</span>
            <Badge variant={dep.status === 'healthy' ? 'default' : 'destructive'}>
              {dep.status}
            </Badge>
          </div>
        ))}
      </div>
    </Card>
  )
}
```

**PerformanceCostCard.tsx:**
```typescript
import { Card } from '@/components/ui/Card'
import { Progress } from '@/components/ui/progress'
import { useOperationsStatus } from '../hooks/useOperationsStatus'

export function PerformanceCostCard() {
  const { data } = useOperationsStatus()

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Performance & Cost</h3>
      <div className="space-y-4">
        <div>
          <div className="flex justify-between mb-2">
            <span>Daily Cost</span>
            <span className={data?.cost.is_near_limit ? 'text-destructive' : ''}>
              ${data?.cost.daily_cost_usd.toFixed(2)} / ${data?.cost.max_daily_cost_usd}
            </span>
          </div>
          <Progress
            value={data?.cost.cost_percentage}
            className={data?.cost.is_near_limit ? 'bg-destructive' : ''}
          />
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-muted-foreground">In-Flight</div>
            <div className="text-2xl font-bold">{data?.performance.in_flight_analyses}</div>
          </div>
          <div>
            <div className="text-muted-foreground">Avg Latency</div>
            <div className="text-2xl font-bold">
              {data?.performance.average_latency_seconds.toFixed(1)}s
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
```

### 3. Configuration Komponenten

**LLMModelManagement.tsx:**
```typescript
import { Card } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getModelConfiguration, updateModelConfiguration } from '@/lib/api/contentAnalysisAdmin'

export function LLMModelManagement() {
  const { data: config } = useQuery({
    queryKey: ['model-configuration'],
    queryFn: getModelConfiguration,
  })

  const queryClient = useQueryClient()
  const updateMutation = useMutation({
    mutationFn: updateModelConfiguration,
    onSuccess: () => {
      queryClient.invalidateQueries(['model-configuration'])
      // Show toast notification
    },
  })

  // Form state management...

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">LLM Model Management</h3>
      {/* Provider dropdowns, overrides table */}
      <Button onClick={() => updateMutation.mutate(formData)}>
        Save Configuration
      </Button>
    </Card>
  )
}
```

**ServiceControls.tsx mit Cache Flush:**
```typescript
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/Button'
import { useMutation } from '@tanstack/react-query'
import { flushCache } from '@/lib/api/contentAnalysisAdmin'

export function ServiceControls() {
  const flushMutation = useMutation({
    mutationFn: flushCache,
    onSuccess: (data) => {
      // Show toast: `Flushed ${data.keys_flushed} keys`
    },
  })

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Service Controls</h3>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          <Button variant="destructive">Flush Cache</Button>
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will clear ALL cached analysis results. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => flushMutation.mutate()}>
              Flush Cache
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  )
}
```

## Testing

### Backend testen:
```bash
cd /home/cytrex/news-microservices
docker compose restart content-analysis-service

# Test operations endpoint
curl -X GET http://localhost:8102/api/v1/internal/status/operations \
  -H "X-Service-Key: ZQnaPRqcelc3IJ-xKXtqrnYxGXLBCOBhDzQhNsaBxZg"

# Test model configuration
curl -X GET http://localhost:8102/api/v1/internal/configuration/models \
  -H "X-Service-Key: ZQnaPRqcelc3IJ-xKXtqrnYxGXLBCOBhDzQhNsaBxZg"
```

### Frontend testen:
```bash
cd /home/cytrex/news-microservices/frontend
npm run dev

# Navigate to: http://localhost:3000/admin/services/content-analysis
```

## Environment Variables

Füge zu `frontend/.env.local` hinzu:
```
VITE_CONTENT_ANALYSIS_API_URL=http://localhost:8102
VITE_CONTENT_ANALYSIS_SERVICE_KEY=ZQnaPRqcelc3IJ-xKXtqrnYxGXLBCOBhDzQhNsaBxZg
```

## Dateistruktur

```
Backend:
services/content-analysis-service/app/
├── schemas/admin.py                    ✅ Neu
├── services/admin_service.py           ✅ Neu
├── services/cache_service.py           ✅ Erweitert
└── api/internal.py                     ✅ Erweitert

Frontend:
frontend/src/
├── types/contentAnalysis.ts            ✅ Neu
├── lib/api/contentAnalysisAdmin.ts     ✅ Neu
├── pages/admin/
│   └── ContentAnalysisAdminPage.tsx    ✅ Neu (Grundgerüst)
├── features/admin/content-analysis/
│   ├── components/
│   │   ├── live-operations/            ⚠️ TODO
│   │   │   ├── CoreDependenciesCard.tsx
│   │   │   ├── EventProcessingCard.tsx
│   │   │   ├── PerformanceCostCard.tsx
│   │   │   └── CachePerformanceCard.tsx
│   │   ├── analysis-explorer/          ⚠️ TODO
│   │   │   ├── OSINTReviewSection.tsx
│   │   │   ├── RecentActivityTable.tsx
│   │   │   └── FailedAnalysisDetails.tsx
│   │   └── configuration/              ⚠️ TODO
│   │       ├── LLMModelManagement.tsx
│   │       └── ServiceControls.tsx
│   └── hooks/                          ⚠️ TODO
│       ├── useOperationsStatus.ts
│       ├── useRecentActivity.ts
│       └── useModelConfiguration.ts
├── components/ui/
│   ├── badge.tsx                       ✅ Neu
│   ├── progress.tsx                    ✅ Neu
│   └── alert-dialog.tsx                ✅ Neu
├── components/layout/MainLayout.tsx    ✅ Erweitert
└── App.tsx                             ✅ Erweitert
```

## Zusammenfassung

### ✅ Fertig (Backend + Infrastruktur):
- Alle Backend API-Endpunkte funktionsfähig
- TypeScript Types & API Client
- Routing & Navigation
- UI-Komponenten installiert
- Grundgerüst der Hauptseite

### ⚠️ Noch zu tun (UI-Komponenten):
- React Query Hooks (3 Dateien, ~20 Zeilen Code pro Datei)
- Live Operations Komponenten (4 Cards)
- Analysis Explorer Komponenten (3 Komponenten)
- Configuration Komponenten (2 Komponenten)

**Geschätzter Aufwand für verbleibende UI-Komponenten:** 2-3 Stunden

Die Architektur ist vollständig definiert, alle APIs funktionieren, und die Beispiele in diesem Dokument zeigen genau, wie die UI-Komponenten implementiert werden sollen.
