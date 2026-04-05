/**
 * Market Feature
 * Centralized exports for all market-related modules
 */

// Types
export * from './types';

// API Hooks
export * from './api';

// Components
export * from './components/earnings';
export * from './components/historical';
export * from './components/macros';

// Hooks
export { useMarketData, useQuotes } from './hooks/useMarketData';
export { useHistoricalData } from './hooks/useHistoricalData';
export { useMacroIndicators } from './hooks/useMacroIndicators';
export { useMarketNews } from './hooks/useMarketNews';

// Pages
export * from './pages';
