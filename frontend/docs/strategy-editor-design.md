# Strategy Editor - Component Design

## Architecture Overview

Based on architectural decisions:
- **Navigation:** Sidebar + Main Panel
- **ML Strategy:** Parallel optimization (all modules simultaneously)
- **Per-Regime Config:** Regime-tabs within each module (uniform across all)
- **Regimes:** TREND, CONSOLIDATION, HIGH_VOLATILITY

## Routing Structure

```
/trading/backtest                          → StrategyLabLandingPage (existing)
/trading/backtest/strategy/:id             → Detail modal (existing)
/trading/backtest/strategy/:id/edit        → StrategyEditorPage (NEW)
```

## Component Hierarchy

```
StrategyEditorPage (Page Container)
├─ Header (Sticky)
│  ├─ Breadcrumbs
│  ├─ Strategy Name + Version Badge
│  └─ Action Buttons (Save, Cancel, Preview)
│
├─ Layout Container (Flex Row)
│  │
│  ├─ Sidebar Navigation (Fixed Width: 280px)
│  │  ├─ NavigationItem: Metadata (icon: FileText)
│  │  ├─ NavigationItem: Regime Detection (icon: TrendingUp)
│  │  ├─ NavigationItem: Entry Logic (icon: ArrowRight)
│  │  ├─ NavigationItem: Exit Logic (icon: X)
│  │  ├─ NavigationItem: Risk Management (icon: Shield)
│  │  ├─ NavigationItem: MTFA (icon: Layers)
│  │  └─ NavigationItem: Protections (icon: Lock)
│  │
│  └─ Main Panel (Flex: 1, Overflow Scroll)
│     ├─ MetadataEditor (No regime tabs)
│     ├─ RegimeDetectionEditor (No regime tabs - global config)
│     ├─ EntryLogicEditor (WITH regime tabs)
│     ├─ ExitLogicEditor (WITH regime tabs)
│     ├─ RiskManagementEditor (WITH regime tabs)
│     ├─ MTFAEditor (No regime tabs - global config)
│     └─ ProtectionsEditor (No regime tabs - global config)
```

## 6 Main Editor Modules

### 1. MetadataEditor (No Regime Tabs)

**Fields:**
- Name (text input)
- Version (text input)
- Description (textarea)
- Author (text input, default: current user)
- Tags (multi-select)
- Is Public (toggle)

**Component:** `MetadataEditor.tsx`

---

### 2. RegimeDetectionEditor (No Regime Tabs - Global Config)

**Purpose:** Configure how market regimes are detected

**Fields:**
- Provider (select: "rule_based", "ml_based", "hybrid")
- Config (JSON schema based on provider):
  - **Rule-Based:**
    - ADX Threshold (number slider: 0-100)
    - BBW Threshold (number slider: 0-1)
    - ATR Threshold (number slider: 0-10)
  - **ML-Based:**
    - Model Path (file picker)
    - Feature Columns (multi-select)
    - Confidence Threshold (number slider: 0-1)
  - **Hybrid:**
    - Rule Weight (number slider: 0-1)
    - ML Weight (number slider: 0-1)
    - Combine Method (select: "weighted_avg", "voting", "sequential")

**ML-Optimizable Parameters:**
- All thresholds
- Feature weights
- Confidence thresholds

**Component:** `RegimeDetectionEditor.tsx`

---

### 3. EntryLogicEditor (WITH Regime Tabs)

**Layout:**
```
┌─────────────────────────────────────────┐
│  ENTRY LOGIC                            │
│  ┌─────┬────────────┬────────────────┐ │
│  │TREND│CONSOLIDATION│HIGH_VOLATILITY│ │ ← Tabs
│  └─────┴────────────┴────────────────┘ │
│                                         │
│  [Per-Regime Form Content]             │
│  - Conditions List (dynamic)           │
│  - Aggregation Mode                    │
│  - Threshold                           │
│  - Description                         │
└─────────────────────────────────────────┘
```

**Per-Regime Fields:**
- **Conditions** (array):
  - Expression (code editor with indicator autocomplete)
  - Description (text input)
  - Confidence Weight (number slider: 0-1)
  - [+ Add Condition button]
- **Aggregation Mode** (select):
  - "ALL" (all conditions must be true)
  - "ANY" (at least one condition must be true)
  - "WEIGHTED" (weighted sum >= threshold)
  - "CONFIDENCE_VOTING" (majority vote weighted by confidence)
- **Threshold** (number slider: 0-1, only for WEIGHTED/CONFIDENCE_VOTING)
- **Description** (textarea)

**Indicators Available (15 total):**
- 1h_RSI_14, 1h_MACD_12_26_9
- 1h_EMA_20, 1h_EMA_50, 1h_EMA_200
- 4h_EMA_50, 4h_EMA_200
- 1d_EMA_50
- 1h_ATR_14, 1h_ADX_14, 1h_BBW_20
- 1h_BB_UPPER_20, 1h_BB_LOWER_20
- 1h_VOLUME, 1h_VOLUME_SMA_20

**ML-Optimizable Parameters:**
- Confidence weights per condition
- Aggregation thresholds
- Indicator periods (e.g., RSI_14 → RSI_?)

**Component:** `EntryLogicEditor.tsx`
**Sub-Components:**
- `ConditionEditor.tsx` (single condition form)
- `ConditionsList.tsx` (array of conditions)
- `IndicatorAutocomplete.tsx` (code editor with indicator hints)

---

### 4. ExitLogicEditor (WITH Regime Tabs)

**Layout:** Same tab structure as Entry Logic

**Per-Regime Fields:**
- **Exit Rules** (array):
  - Type (select):
    - "take_profit" (fixed %)
    - "trailing_stop" (dynamic)
    - "stop_loss" (fixed %)
    - "time_based" (max bars)
    - "regime_change" (exit when regime changes)
    - "indicator_signal" (RSI normalization, etc.)
  - Type-Specific Fields:
    - **take_profit:** value (%)
    - **trailing_stop:** activation (%), offset (%)
    - **stop_loss:** value (%)
    - **time_based:** maxBars (number)
    - **regime_change:** action (close all / close partial)
    - **indicator_signal:** expression (code editor)
  - Description (text input)
  - [+ Add Exit Rule button]

**ML-Optimizable Parameters:**
- Take profit %
- Trailing stop activation/offset
- Time-based max bars
- Indicator signal thresholds

**Component:** `ExitLogicEditor.tsx`
**Sub-Components:**
- `ExitRuleEditor.tsx` (single rule form)
- `ExitRulesList.tsx` (array of rules)

---

### 5. RiskManagementEditor (WITH Regime Tabs)

**Layout:** Same tab structure as Entry/Exit Logic

**Per-Regime Fields:** 3 Sub-Sections (Accordion or Tabs within Tabs)

#### 5a. Stop Loss Configuration
- **Dynamic** (toggle)
- **Formula** (code editor):
  - Default: `entry_price - (2.0 * 1h_ATR_14)`
  - Indicators: ATR_14, BB_MIDDLE_20
- **Description** (text input)
- **Trailing Stop** (sub-section):
  - Enabled (toggle)
  - Callback (select: "custom_stoploss", "default")
  - Activation (number slider: 0-1, e.g., 0.01 = 1%)

**ML-Optimizable:**
- ATR multiplier (e.g., 2.0 → ?)
- Trailing activation threshold

#### 5b. Position Sizing Configuration
- **Method** (select):
  - "percent_risk" (risk fixed % per trade)
  - "kelly_criterion" (Kelly fraction)
  - "volatility_based" (ATR-based sizing)
- **Formula** (code editor):
  - Default: `(account_balance * 0.01) / ((2.0 * 1h_ATR_14) / entry_price)`
- **Description** (text input)
- **Max Risk Per Trade** (number slider: 0-0.05, e.g., 0.01 = 1%)

**ML-Optimizable:**
- Risk % (0.01 → ?)
- ATR multiplier for stop distance
- Kelly fraction

#### 5c. Leverage Configuration
- **Max** (number slider: 1-10)
- **Min** (number slider: 1-10)
- **Formula** (code editor):
  - Default: `Min(3.0, Max(1.0, 3.0 * (1h_ADX_14 / 40)))`
  - Indicators: ADX_14, BBW_20
- **Description** (text input)

**ML-Optimizable:**
- Max leverage (3.0 → ?)
- ADX divisor (40 → ?)
- Formula coefficients

**Component:** `RiskManagementEditor.tsx`
**Sub-Components:**
- `StopLossConfig.tsx`
- `PositionSizeConfig.tsx`
- `LeverageConfig.tsx`

---

### 6. MTFAEditor (No Regime Tabs - Global Config)

**Purpose:** Multi-Timeframe Analysis configuration

**Fields:**
- **Timeframes** (list):
  - 1h (primary, non-removable)
  - 4h (confirmation)
  - 1d (macro filter)
- **Per-Timeframe Config:**
  - Indicators Used (multi-select from available indicators)
  - Weight (number slider: 0-1)
  - Divergence Threshold (number slider: 0-1)
  - Description (text input)

**ML-Optimizable:**
- Timeframe weights
- Divergence thresholds

**Component:** `MTFAEditor.tsx`

---

### 7. ProtectionsEditor (No Regime Tabs - Global Config)

**Purpose:** Global safeguards (overrides all regimes)

**Fields:**
- **Protection Rules** (array):
  - Type (select):
    - "StoplossGuard" (prevent trades after stop losses)
    - "MaxDrawdown" (pause trading at max DD)
    - "LowProfitPairs" (blacklist low-performing symbols)
    - "CooldownPeriod" (pause after consecutive losses)
  - Type-Specific Fields:
    - **StoplossGuard:**
      - Trade Limit (number: max stop losses)
      - Stop Duration (number: minutes to pause)
      - Lookback Period (number: minutes to check)
    - **MaxDrawdown:**
      - Max Allowed Drawdown (number slider: 0-1, e.g., 0.2 = 20%)
    - **LowProfitPairs:**
      - Required Profit (number slider: 0-1, e.g., 0.005 = 0.5%)
      - Lookback Trades (number)
    - **CooldownPeriod:**
      - Stop Duration (number: minutes)
      - Lookback Period (number: minutes)
  - Description (text input)
  - [+ Add Protection button]

**ML-Optimizable:**
- All thresholds (trade limits, DD %, profit requirements)
- Lookback periods
- Stop durations

**Component:** `ProtectionsEditor.tsx`
**Sub-Components:**
- `ProtectionRuleEditor.tsx`

---

## Shared Components

### RegimeTabs Component (Reusable)

**Usage:**
```tsx
<RegimeTabs
  regimes={['TREND', 'CONSOLIDATION', 'HIGH_VOLATILITY']}
  defaultRegime="TREND"
  renderContent={(regime) => <EntryLogicForm regime={regime} />}
/>
```

**Props:**
- `regimes: RegimeType[]` (TREND, CONSOLIDATION, HIGH_VOLATILITY)
- `defaultRegime: RegimeType`
- `renderContent: (regime: RegimeType) => ReactNode`

**Component:** `RegimeTabs.tsx`

---

### CodeEditor Component (For Formulas/Expressions)

**Usage:**
```tsx
<CodeEditor
  value={formula}
  onChange={setFormula}
  language="python"
  availableIndicators={indicators}
  placeholder="entry_price - (2.0 * 1h_ATR_14)"
/>
```

**Features:**
- Syntax highlighting
- Indicator autocomplete
- Validation (SymPy compatibility)
- Error highlighting

**Component:** `CodeEditor.tsx`

---

## Form State Management

### Approach: React Hook Form + Zod

**Why:**
- Type-safe validation
- Deep object nesting (per-regime configs)
- Array fields (conditions, rules)
- Optimistic updates

**Schema Structure:**
```typescript
const strategyEditorSchema = z.object({
  // Metadata
  name: z.string().min(1),
  version: z.string().regex(/^\d+\.\d+\.\d+$/),
  description: z.string().optional(),
  author: z.string(),
  tags: z.array(z.string()),
  is_public: z.boolean(),

  // Definition
  definition: z.object({
    // Regime Detection
    regimeDetection: z.object({
      provider: z.enum(['rule_based', 'ml_based', 'hybrid']),
      config: z.record(z.any()), // Dynamic schema based on provider
    }),

    // Indicators (global)
    indicators: z.array(indicatorSchema),

    // Logic (per-regime)
    logic: z.object({
      TREND: regimeLogicSchema,
      CONSOLIDATION: regimeLogicSchema,
      HIGH_VOLATILITY: regimeLogicSchema,
    }),

    // MTFA
    mtfa: z.object({
      timeframes: z.array(timeframeConfigSchema),
    }),

    // Protections
    protections: z.array(protectionRuleSchema),
  }),
})

const regimeLogicSchema = z.object({
  entry: z.object({
    conditions: z.array(conditionSchema),
    aggregation: z.enum(['ALL', 'ANY', 'WEIGHTED', 'CONFIDENCE_VOTING']),
    threshold: z.number().min(0).max(1).optional(),
    description: z.string().optional(),
  }),
  exit: z.object({
    rules: z.array(exitRuleSchema),
  }),
  risk: z.object({
    stopLoss: stopLossSchema,
    positionSize: positionSizeSchema,
    leverage: leverageSchema,
  }),
})
```

**Form Hook:**
```typescript
const form = useForm<StrategyFormData>({
  resolver: zodResolver(strategyEditorSchema),
  defaultValues: strategy.definition,
})
```

---

## API Integration

### Endpoints

```typescript
// GET strategy for editing
GET /api/v1/strategies/:id
Response: Strategy

// UPDATE strategy
PUT /api/v1/strategies/:id
Body: StrategyFormData
Response: Strategy

// VALIDATE strategy (before save)
POST /api/v1/strategies/validate
Body: StrategyFormData
Response: ValidationResult
```

### Save Workflow

1. User clicks "Save"
2. Form validation (client-side Zod)
3. If valid → API validation (POST /validate)
4. If server validation passes → PUT /strategies/:id
5. Optimistic update (React Query)
6. On success: Navigate to detail view
7. On error: Show error toast + rollback

**Component:** `StrategyEditorPage.tsx`

---

## File Structure

```
src/features/trading/
├─ pages/
│  ├─ StrategyLabLandingPage.tsx (existing)
│  └─ StrategyEditorPage.tsx (NEW)
│
├─ components/
│  ├─ StrategyDetailModal.tsx (existing)
│  │
│  ├─ editor/ (NEW)
│  │  ├─ EditorSidebar.tsx
│  │  ├─ EditorHeader.tsx
│  │  ├─ MetadataEditor.tsx
│  │  ├─ RegimeDetectionEditor.tsx
│  │  ├─ EntryLogicEditor.tsx
│  │  ├─ ExitLogicEditor.tsx
│  │  ├─ RiskManagementEditor.tsx
│  │  ├─ MTFAEditor.tsx
│  │  ├─ ProtectionsEditor.tsx
│  │  │
│  │  ├─ shared/
│  │  │  ├─ RegimeTabs.tsx
│  │  │  ├─ CodeEditor.tsx
│  │  │  ├─ ConditionEditor.tsx
│  │  │  ├─ ExitRuleEditor.tsx
│  │  │  └─ ProtectionRuleEditor.tsx
│  │  │
│  │  └─ risk/
│  │     ├─ StopLossConfig.tsx
│  │     ├─ PositionSizeConfig.tsx
│  │     └─ LeverageConfig.tsx
│  │
│  └─ strategy/ (existing - read-only sections)
│     ├─ MetadataSection.tsx
│     ├─ RegimeDetectionSection.tsx
│     ├─ IndicatorsSection.tsx
│     └─ LogicSection.tsx
│
├─ schemas/
│  └─ strategyEditorSchema.ts (Zod schemas)
│
└─ hooks/
   ├─ useStrategyEditor.ts (form state management)
   └─ useStrategyValidation.ts (API validation)
```

---

## Implementation Priority

### Phase 1: Core Structure (Days 1-2)
1. ✅ Create StrategyEditorPage.tsx
2. ✅ Create EditorSidebar.tsx
3. ✅ Create EditorHeader.tsx
4. ✅ Create RegimeTabs.tsx (shared)
5. ✅ Setup React Hook Form + Zod schema

### Phase 2: Simple Editors (Days 3-4)
6. ✅ MetadataEditor.tsx
7. ✅ RegimeDetectionEditor.tsx
8. ✅ MTFAEditor.tsx
9. ✅ ProtectionsEditor.tsx

### Phase 3: Complex Editors (Days 5-7)
10. ✅ EntryLogicEditor.tsx + ConditionEditor.tsx
11. ✅ ExitLogicEditor.tsx + ExitRuleEditor.tsx
12. ✅ RiskManagementEditor.tsx + sub-configs

### Phase 4: Code Editor (Day 8)
13. ✅ CodeEditor.tsx with indicator autocomplete
14. ✅ SymPy validation integration

### Phase 5: API Integration (Day 9)
15. ✅ Save/Cancel workflows
16. ✅ Validation endpoints
17. ✅ Optimistic updates

### Phase 6: Testing (Day 10)
18. ✅ Unit tests for editors
19. ✅ Integration tests for save workflow
20. ✅ E2E tests with real strategy

---

## ML Optimization UI (Future - Phase 7)

**Not part of initial editor, but planned:**

Each module will have an "Optimize" button that:
1. Shows optimization modal
2. Allows selecting parameters to optimize
3. Configures optimization method (Hyperopt, WFO, Grid Search)
4. Runs optimization job (async)
5. Shows results and allows applying best parameters

**This will be a separate feature after the editor is complete.**

---

## Visual Design Notes

### Color Coding by Regime
- TREND: Green accent (`text-green-500`, `border-green-500`)
- CONSOLIDATION: Blue accent (`text-blue-500`, `border-blue-500`)
- HIGH_VOLATILITY: Orange accent (`text-orange-500`, `border-orange-500`)

### Icons per Module
- Metadata: `FileText`
- Regime Detection: `TrendingUp`
- Entry Logic: `ArrowRight`
- Exit Logic: `X`
- Risk Management: `Shield`
- MTFA: `Layers`
- Protections: `Lock`

### Spacing
- Sidebar width: 280px (fixed)
- Main panel padding: 24px
- Section spacing: 32px (space-y-8)
- Form field spacing: 16px (space-y-4)

---

## Next Steps

1. ✅ Create TodoWrite list (DONE)
2. Create StrategyEditorPage.tsx skeleton
3. Create EditorSidebar.tsx
4. Create RegimeTabs.tsx (shared component)
5. Setup Zod schema in strategyEditorSchema.ts
6. Implement MetadataEditor.tsx (simplest module)
7. Continue with remaining modules in priority order
