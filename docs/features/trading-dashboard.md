# Trading Dashboard - Professional Crypto Trading Terminal

**Status:** ✅ Production Ready (Implemented 2025-11-29)
**Location:** `frontend/src/features/trading/`
**Access:** http://localhost:3000/trading
**Services:** execution-service (8120), prediction-service (8116)

---

## Overview

Bybit/Binance-inspired dark theme trading terminal for real-time position monitoring and emergency controls. Provides live portfolio metrics, position tracking, and panic controls for automated trading strategies.

### Key Features

- **Real-time Portfolio Metrics** - Auto-refresh every 5 seconds
- **Live Position Tracking** - Open positions with unrealized P&L
- **Emergency Controls** - Panic button to close all positions
- **Dark Theme UI** - Professional crypto exchange aesthetic
- **TradingView-style Charts** - Price visualization (placeholder for Phase 3)

---

## Architecture

### Tech Stack

```
Frontend (React 19 + TypeScript)
├── Vite (Build tool, HMR)
├── Tailwind CSS (Styling)
├── TanStack Query (Server state management)
├── Lucide React (Icons)
└── Lightweight Charts (TradingView charts - planned)

Backend Services
├── execution-service (8120) - Position management, portfolio
└── prediction-service (8116) - Trading signals, strategy analysis
```

### Component Structure

```
src/features/trading/
├── pages/
│   └── TradingDashboard.tsx       # Main dashboard page
├── components/
│   ├── MetricCard.tsx             # KPI display cards
│   ├── PriceChart.tsx             # TradingView-style chart
│   ├── PositionsTable.tsx         # Live positions table
│   └── PanicButton.tsx            # Emergency close all
└── hooks/
    └── useTrading.ts (via src/hooks/)

src/lib/api/
└── trading.ts                      # API client (axios instances)
```

---

## API Integration

### Environment Configuration

**File:** `frontend/.env`

```bash
# Trading Services
VITE_PREDICTION_API_URL=http://localhost:8116/api/v1
VITE_EXECUTION_API_URL=http://localhost:8120/api/v1
```

**Note:** Uses host IP (localhost) instead of localhost for network access from other devices.

### API Client

**File:** `src/lib/api/trading.ts`

```typescript
// Axios instances
export const executionApi = axios.create({
  baseURL: import.meta.env.VITE_EXECUTION_API_URL || 'http://localhost:8120/api/v1'
})

export const predictionApi = axios.create({
  baseURL: import.meta.env.VITE_PREDICTION_API_URL || 'http://localhost:8116/api/v1'
})

// Methods
tradingApi.getPositions()        // All positions
tradingApi.getOpenPositions()    // Open positions only
tradingApi.getPortfolio()        // Balance, equity, P&L
tradingApi.closePosition(id)     // Close single position
tradingApi.closeAllPositions()   // Panic - close all
tradingApi.stopTrading()         // Halt signal processing
tradingApi.resumeTrading()       // Resume signal processing
```

### TypeScript Interfaces

```typescript
interface Position {
  id: string
  symbol: string
  side: 'long' | 'short'
  status: 'open' | 'closed' | 'pending'
  entry_price: number
  stop_loss: number | null
  take_profit: number | null
  quantity: number
  notional_value: number
  unrealized_pnl?: number
  realized_pnl?: number
  created_at: string
  closed_at?: string | null
}

interface Portfolio {
  balance: {
    initial: number
    current: number
    note?: string
  }
  equity: number
  unrealized_pnl: number
  realized_pnl: number
  open_positions: number
  margin_used: number
  margin_available: number
}
```

**⚠️ Important:** `balance` is a nested object with `current`, `initial`, and `note` properties.

---

## React Query Hooks

**File:** `src/hooks/useTrading.ts`

### Auto-Refresh Queries

```typescript
usePortfolio()        // Refresh every 5s
usePositions()        // Refresh every 5s
useOpenPositions()    // Refresh every 5s
useSystemStatus()     // Refresh every 10s
```

### Mutations with Cache Invalidation

```typescript
useClosePosition()        // Invalidates: positions, portfolio
useCloseAllPositions()    // Invalidates: positions, portfolio
useStopTrading()          // Invalidates: systemStatus
useResumeTrading()        // Invalidates: systemStatus
```

**Pattern:** All mutations automatically invalidate relevant queries for optimistic updates.

---

## Components

### 1. TradingDashboard (Main Page)

**File:** `src/features/trading/pages/TradingDashboard.tsx`

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Trading Terminal                          [PANIC CLOSE ALL] │
│ Real-time execution monitor                                 │
├─────────────────────────────────────────────────────────────┤
│ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐                   │
│ │Balance│ │Unreal │ │  Open │ │Realiz │                   │
│ │$9,965 │ │P&L    │ │  Pos  │ │P&L    │                   │
│ └───────┘ └───────┘ └───────┘ └───────┘                   │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────────┐ ┌─────────────┐                       │
│ │                  │ │  Positions  │                       │
│ │  Price Chart     │ │  Table      │                       │
│ │  (2/3 width)     │ │  (1/3 width)│                       │
│ └──────────────────┘ └─────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

**Critical Fix - Defensive Destructuring:**

```typescript
// ⚠️ IMPORTANT: Handle nested balance structure
const balance = portfolio?.balance?.current ?? 0  // Not portfolio?.balance ?? 0
const equity = portfolio?.equity ?? 0
const unrealizedPnl = portfolio?.unrealized_pnl ?? 0
const realizedPnl = portfolio?.realized_pnl ?? 0
const openPositions = portfolio?.open_positions ?? 0
const marginUsed = portfolio?.margin_used ?? 0

// Now all values are guaranteed numbers - .toFixed() is safe
value={`$${balance.toFixed(2)}`}
```

**Why:** Backend returns `balance` as an object `{initial, current, note}`, not a simple number.

### 2. MetricCard (KPI Display)

**File:** `src/features/trading/components/MetricCard.tsx`

**Props:**
```typescript
interface MetricCardProps {
  title: string
  value: string | number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
  icon?: React.ReactNode
}
```

**Styling:**
- Dark background: `#1A1F2E`
- Cyan highlights: `#00D4FF`
- Trend indicators: Green (up), Red (down), Gray (neutral)

### 3. PositionsTable (Live Positions)

**File:** `src/features/trading/components/PositionsTable.tsx`

**Features:**
- Auto-refresh every 5 seconds
- Loading states with spinner
- Error handling display
- Close button per position
- Confirmation dialog before close

**Data Flow:**
```typescript
const { data, isLoading, error } = useOpenPositions()
const closePosition = useClosePosition()

const handleClose = async (positionId: string) => {
  if (confirm('Close this position?')) {
    await closePosition.mutateAsync(positionId)
  }
}
```

### 4. PanicButton (Emergency Controls)

**File:** `src/features/trading/components/PanicButton.tsx`

**Features:**
- Red, pulsing animation (`animate-pulse`)
- Confirmation dialog before execution
- Loading state during API call
- Error handling with user feedback

**Styling:**
```typescript
className="bg-[#EF5350] hover:bg-[#D32F2F] text-white font-bold
           shadow-lg shadow-red-500/50 animate-pulse"
```

**Safety:**
```typescript
const handlePanic = async () => {
  try {
    await closeAll.mutateAsync()
    console.log('✅ All positions closed successfully')
    setShowConfirm(false)
  } catch (error) {
    console.error('❌ Failed to close all positions:', error)
    alert('Failed to close positions. Check console for details.')
  }
}
```

---

## Styling & Theme

### Dark Theme Configuration

**File:** `tailwind.config.js`

```javascript
theme: {
  extend: {
    colors: {
      background: '#0B0E11',      // Main background
      card: '#1A1F2E',            // Card backgrounds
      primary: '#00D4FF',         // Cyan highlights
      success: '#26A69A',         // Green (profit)
      danger: '#EF5350',          // Red (loss/panic)
      muted: '#6B7280',           // Gray text
    }
  }
}
```

### Design Inspiration

- **Bybit/Binance Dark Mode** - Professional crypto exchange aesthetic
- **TradingView** - Chart styling and layout
- **Charcoal backgrounds** with cyan/blue highlights
- **Minimal borders** - Focus on content
- **Professional typography** - Clear hierarchy

---

## Development Workflow

### Start Development

```bash
# Start all services
cd /home/cytrex/news-microservices
docker compose up -d

# Frontend auto-reloads on file changes (Vite HMR)
# Edit files in frontend/src/features/trading/*
# Changes appear in browser < 1 second
```

### Access Points

- **Main App:** http://localhost:3000
- **Trading Dashboard:** http://localhost:3000/trading
- **execution-service API:** http://localhost:8120/docs
- **prediction-service API:** http://localhost:8116/docs

### Test API Endpoints

```bash
# Portfolio data
curl http://localhost:8120/api/v1/portfolio | jq

# Open positions
curl http://localhost:8120/api/v1/positions?status=open | jq

# System health
curl http://localhost:8120/api/v1/health | jq
```

---

## Troubleshooting

### Issue: `$[object Object]` displayed instead of balance

**Cause:** Backend returns nested balance structure `{initial, current, note}`

**Fix:**
```typescript
// ❌ Wrong
const balance = portfolio?.balance ?? 0

// ✅ Correct
const balance = portfolio?.balance?.current ?? 0
```

### Issue: `TypeError: Cannot read properties of undefined (reading 'toFixed')`

**Cause:** Optional chaining doesn't prevent method calls on undefined

**Fix:** Use nullish coalescing to guarantee non-undefined values
```typescript
// ❌ Wrong - can crash
portfolio?.unrealized_pnl.toFixed(2)

// ✅ Correct - safe
const unrealizedPnl = portfolio?.unrealized_pnl ?? 0
unrealizedPnl.toFixed(2)
```

### Issue: Connection refused (ERR_CONNECTION_REFUSED)

**Cause:** Using `localhost` URLs when accessing from different machine

**Fix:** Use host IP in `.env` file
```bash
# Instead of localhost
VITE_EXECUTION_API_URL=http://localhost:8120/api/v1
```

### Issue: Environment variables not loading

**Solution:**
1. Create `frontend/.env` file (Vite loads this automatically)
2. Restart frontend container: `docker compose restart frontend`
3. Hard refresh browser: `Ctrl+Shift+R`

### Browser Console Warnings

**Warning:** `Unchecked runtime.lastError: The message port closed before a response was received`

**Explanation:** Browser extension warning, **not an application error**. Safe to ignore.

---

## Performance

### Auto-Refresh Rates

| Query | Interval | Reasoning |
|-------|----------|-----------|
| Portfolio | 5s | Balance changes with position updates |
| Positions | 5s | Real-time trading requires quick updates |
| System Status | 10s | Infrastructure changes are less frequent |

### Optimization Strategies

1. **Query Deduplication** - TanStack Query deduplicates parallel requests
2. **Automatic Cache Invalidation** - Mutations trigger refetch only for affected data
3. **Optimistic Updates** - UI updates immediately, rolls back on error
4. **Stale While Revalidate** - Shows cached data while fetching fresh data

---

## Future Enhancements (Phase 3)

### 1. Real TradingView Charts
- Replace placeholder with `lightweight-charts` library
- Live price data from Bybit WebSocket
- Multiple timeframes (1m, 5m, 15m, 1h, 4h, 1D)
- Technical indicators (MA, RSI, MACD)

### 2. Advanced Position Management
- Modify stop-loss/take-profit
- Partial position closure
- Position history timeline
- Risk/reward calculator

### 3. Trading Controls
- Manual order placement
- Strategy on/off toggles
- Risk parameter adjustment
- Position sizing calculator

### 4. Analytics & Reporting
- Performance metrics (win rate, profit factor, Sharpe ratio)
- Drawdown charts
- Trade journal
- Export to CSV/Excel

---

## Related Documentation

- [execution-service README](../services/execution-service.md)
- [prediction-service README](../services/prediction-service.md)
- [Frontend Development Guide](../../CLAUDE.frontend.md)
- [API Documentation](http://localhost:8120/docs)

---

## Changelog

### 2025-11-29 - Initial Implementation

**Added:**
- Trading Dashboard page with real-time metrics
- API client for execution-service and prediction-service
- TanStack Query hooks with auto-refresh
- Positions table with live data
- Panic button with confirmation dialog
- Dark theme styling (Bybit/Binance-inspired)

**Fixed:**
- Nested balance object handling (`balance.current`)
- TypeScript interface for Portfolio (nested structure)
- Environment variables for network access (host IP)
- Defensive destructuring for runtime safety

**Status:** ✅ Production Ready

---

**Last Updated:** 2025-11-29
**Maintainer:** Andreas
**Version:** 1.0.0
