# Trading Dashboard Feature

**Status:** ⚠️ Under Construction (2025-12-28)
**Access:** http://localhost:3000/trading

---

## Current Status

### Archived: execution-service (Port 8120)

The execution-service which provided:
- Position management
- Portfolio tracking
- Kill switch / Trading control
- Strategy performance leaderboard

has been **archived** on 2025-12-28.

### What's Working

- **ML Lab** (`/trading/ml-lab`) - Model training, backtesting, live inference
- **Strategy Lab** (`/trading/strategy-lab`) - Strategy development, walk-forward validation
- **Market Data** - Via prediction-service and FMP service

### What's Being Rebuilt

Trading execution features will be integrated into the prediction-service as part of the ongoing refactoring.

See: `services/prediction-service/REFACTORING_PROMPT.md`

---

## Files Structure

```
trading/
├── pages/
│   ├── TradingDashboard.tsx       # ⚠️ Placeholder (Under Construction)
│   ├── AnalyticsDashboard.tsx     # ⚠️ Placeholder (Under Construction)
│   └── ...other pages             # ML Lab, Strategy Lab (working)
├── components/
│   ├── AutopilotControl.tsx       # ML Lab autopilot control
│   ├── DebugLogViewer.tsx         # Strategy debugging
│   └── ...                        # Other components
└── README.md                      # This file
```

---

## API Integration

### Active Service

**prediction-service (8116)** - Strategy analysis, signals, ML Lab
```typescript
import { predictionApi } from '@/lib/api/trading'

// Use predictionApi for all trading-related requests
const response = await predictionApi.get('/strategies')
```

### Removed Service

**execution-service (8120)** - ARCHIVED
- `executionApi` - Removed from `src/lib/api/trading.ts`
- `executionClient` - Removed from `src/lib/api-client.ts`
- Proxy config removed from `vite.config.ts` and `nginx.conf`

---

## Migration Notes

When the prediction-service refactoring is complete, the following features will need new frontend integration:

1. **Position Management**
   - Open/close positions
   - Position list with P&L tracking

2. **Portfolio Dashboard**
   - Balance, equity, margin tracking
   - Daily P&L summary

3. **Trading Controls**
   - Enable/disable trading
   - Kill switch / daily loss limit
   - Circuit breaker status

4. **Strategy Analytics**
   - Multi-strategy leaderboard
   - Win rate, profit factor metrics

---

## For Developers

If you need trading execution features before the rebuild is complete, check:
- `services/prediction-service/REFACTORING_PROMPT.md` - Refactoring plan
- `services/prediction-service/FUNCTIONAL_ANALYSIS_20251228.md` - Current capabilities

---

**Last Updated:** 2025-12-28
**Version:** 2.0.0 (Post-execution-service archive)
