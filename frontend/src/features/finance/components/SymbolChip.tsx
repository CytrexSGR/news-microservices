/**
 * SymbolChip Component
 *
 * Badge component for displaying asset type or market status
 * Used in: Prices, Market Hours, Symbol Search sections
 */

import type { AssetType, MarketStatus } from '../types/market.types';

interface AssetTypeChipProps {
  type: 'asset';
  value: AssetType;
}

interface MarketStatusChipProps {
  type: 'status';
  value: MarketStatus;
}

type SymbolChipProps = AssetTypeChipProps | MarketStatusChipProps;

const assetTypeConfig = {
  crypto: {
    label: 'CRYPTO',
    className: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  },
  forex: {
    label: 'FOREX',
    className: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  },
  indices: {
    label: 'INDEX',
    className: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  },
  commodities: {
    label: 'COMMODITY',
    className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  },
};

const marketStatusConfig = {
  open: {
    label: '✅ OPEN',
    className: 'bg-green-500/20 text-green-400 border-green-500/30',
  },
  closed: {
    label: '⏸️ CLOSED',
    className: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  },
  pre_market: {
    label: '🔜 PRE-MARKET',
    className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  },
  after_hours: {
    label: '🌙 AFTER HOURS',
    className: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  },
};

export function SymbolChip(props: SymbolChipProps) {
  if (props.type === 'asset') {
    const config = assetTypeConfig[props.value];
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold border ${config.className}`}
      >
        {config.label}
      </span>
    );
  }

  if (props.type === 'status') {
    const config = marketStatusConfig[props.value];
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded text-xs font-bold border ${config.className}`}
      >
        {config.label}
      </span>
    );
  }

  return null;
}
