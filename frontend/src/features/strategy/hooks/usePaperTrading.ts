/**
 * usePaperTrading Hook
 *
 * Manages paper trading sessions for a strategy.
 * Connects to the Paper Trading API (prediction-service).
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

// ============================================================================
// Types
// ============================================================================

export interface PaperTradeSession {
  id: string;
  strategy_id: string;
  symbol: string;
  status: 'running' | 'in_position';
  pnl: number;
  pnl_percent: number;
  trades: number;
  win_rate: number;
  current_position: {
    direction: 'long' | 'short';
    entry_price: number;
    size: number;
    entry_time: string;
  } | null;
  last_price: number;
  created_at: string;
  last_tick: string;
}

export interface SessionListResponse {
  sessions: PaperTradeSession[];
  total: number;
}

export interface TickResponse {
  session_id: string;
  symbol: string;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  unrealized_pnl: number;
  position: PaperTradeSession['current_position'];
  signal: string | null;
}

export interface CreateSessionParams {
  strategy_id: string;
  symbol: string;
  initial_capital?: number;
}

// ============================================================================
// API Functions
// ============================================================================

const API_BASE = '/api/prediction/v1/paper-trading';

async function fetchSessions(strategyId?: string): Promise<SessionListResponse> {
  const url = strategyId
    ? `${API_BASE}/sessions?strategy_id=${strategyId}`
    : `${API_BASE}/sessions`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch sessions' }));
    throw new Error(error.detail || 'Failed to fetch sessions');
  }

  return response.json();
}

async function createSession(params: CreateSessionParams): Promise<PaperTradeSession> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create session' }));
    throw new Error(error.detail || 'Failed to create session');
  }

  return response.json();
}

async function stopSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to stop session' }));
    throw new Error(error.detail || 'Failed to stop session');
  }
}

async function stopAllSessions(strategyId?: string): Promise<void> {
  const url = strategyId
    ? `${API_BASE}/sessions?strategy_id=${strategyId}`
    : `${API_BASE}/sessions`;

  const response = await fetch(url, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to stop sessions' }));
    throw new Error(error.detail || 'Failed to stop sessions');
  }
}

async function processTick(sessionId: string): Promise<TickResponse> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/tick`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to process tick' }));
    throw new Error(error.detail || 'Failed to process tick');
  }

  return response.json();
}

async function enterPosition(
  sessionId: string,
  direction: 'long' | 'short',
  size: number = 0.1
): Promise<{ session: PaperTradeSession }> {
  const response = await fetch(
    `${API_BASE}/sessions/${sessionId}/enter?direction=${direction}&size=${size}`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to enter position' }));
    throw new Error(error.detail || 'Failed to enter position');
  }

  return response.json();
}

async function exitPosition(sessionId: string): Promise<{ session: PaperTradeSession }> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/exit`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to exit position' }));
    throw new Error(error.detail || 'Failed to exit position');
  }

  return response.json();
}

// ============================================================================
// Hook
// ============================================================================

export interface UsePaperTradingOptions {
  strategyId: string;
  autoTickInterval?: number; // ms, default 5000 (5 seconds)
  enabled?: boolean;
}

export function usePaperTrading({
  strategyId,
  autoTickInterval = 5000,
  enabled = true,
}: UsePaperTradingOptions) {
  const queryClient = useQueryClient();
  const [autoTick, setAutoTick] = useState(false);
  const tickIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // ============================================================================
  // Query: Fetch sessions
  // ============================================================================
  const {
    data: sessionsData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['paper-trading-sessions', strategyId],
    queryFn: () => fetchSessions(strategyId),
    enabled: enabled && !!strategyId,
    refetchInterval: autoTick ? false : 30000, // Refetch every 30s if not auto-ticking
  });

  const sessions = sessionsData?.sessions || [];

  // ============================================================================
  // Mutations
  // ============================================================================

  const createSessionMutation = useMutation({
    mutationFn: createSession,
    onSuccess: (newSession) => {
      queryClient.setQueryData<SessionListResponse>(
        ['paper-trading-sessions', strategyId],
        (old) => ({
          sessions: [...(old?.sessions || []), newSession],
          total: (old?.total || 0) + 1,
        })
      );
      toast.success(`Started paper trading ${newSession.symbol}`);
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });

  const stopSessionMutation = useMutation({
    mutationFn: stopSession,
    onSuccess: (_, sessionId) => {
      queryClient.setQueryData<SessionListResponse>(
        ['paper-trading-sessions', strategyId],
        (old) => ({
          sessions: (old?.sessions || []).filter((s) => s.id !== sessionId),
          total: Math.max(0, (old?.total || 0) - 1),
        })
      );
      toast.success('Session stopped');
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });

  const stopAllSessionsMutation = useMutation({
    mutationFn: () => stopAllSessions(strategyId),
    onSuccess: () => {
      queryClient.setQueryData<SessionListResponse>(
        ['paper-trading-sessions', strategyId],
        { sessions: [], total: 0 }
      );
      toast.success('All sessions stopped');
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });

  const tickMutation = useMutation({
    mutationFn: processTick,
    onSuccess: (tickData) => {
      // Update the session with new tick data
      queryClient.setQueryData<SessionListResponse>(
        ['paper-trading-sessions', strategyId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            sessions: old.sessions.map((s) =>
              s.id === tickData.session_id
                ? {
                    ...s,
                    last_price: tickData.current_price,
                    pnl: tickData.pnl,
                    pnl_percent: tickData.pnl_percent,
                    current_position: tickData.position,
                    last_tick: new Date().toISOString(),
                  }
                : s
            ),
          };
        }
      );
    },
  });

  const enterPositionMutation = useMutation({
    mutationFn: ({ sessionId, direction, size }: { sessionId: string; direction: 'long' | 'short'; size?: number }) =>
      enterPosition(sessionId, direction, size),
    onSuccess: (data) => {
      queryClient.setQueryData<SessionListResponse>(
        ['paper-trading-sessions', strategyId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            sessions: old.sessions.map((s) =>
              s.id === data.session.id ? data.session : s
            ),
          };
        }
      );
      toast.success(`Entered ${data.session.current_position?.direction} position`);
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });

  const exitPositionMutation = useMutation({
    mutationFn: exitPosition,
    onSuccess: (data) => {
      queryClient.setQueryData<SessionListResponse>(
        ['paper-trading-sessions', strategyId],
        (old) => {
          if (!old) return old;
          return {
            ...old,
            sessions: old.sessions.map((s) =>
              s.id === data.session.id ? data.session : s
            ),
          };
        }
      );
      toast.success('Position closed');
    },
    onError: (err: Error) => {
      toast.error(err.message);
    },
  });

  // ============================================================================
  // Auto-tick effect
  // ============================================================================

  const tickAllSessions = useCallback(async () => {
    if (sessions.length === 0) return;

    // Process ticks for all sessions in parallel
    await Promise.allSettled(
      sessions.map((session) => tickMutation.mutateAsync(session.id))
    );
  }, [sessions, tickMutation]);

  useEffect(() => {
    if (autoTick && sessions.length > 0) {
      // Initial tick
      tickAllSessions();

      // Set up interval
      tickIntervalRef.current = setInterval(tickAllSessions, autoTickInterval);
    }

    return () => {
      if (tickIntervalRef.current) {
        clearInterval(tickIntervalRef.current);
        tickIntervalRef.current = null;
      }
    };
  }, [autoTick, sessions.length, autoTickInterval, tickAllSessions]);

  // ============================================================================
  // Helper functions
  // ============================================================================

  const startSession = useCallback(
    (symbol: string, initialCapital: number = 10000) => {
      createSessionMutation.mutate({
        strategy_id: strategyId,
        symbol,
        initial_capital: initialCapital,
      });
    },
    [createSessionMutation, strategyId]
  );

  const manualTick = useCallback(
    (sessionId: string) => {
      tickMutation.mutate(sessionId);
    },
    [tickMutation]
  );

  // ============================================================================
  // Computed values
  // ============================================================================

  const totalPnl = sessions.reduce((sum, s) => sum + s.pnl, 0);
  const totalTrades = sessions.reduce((sum, s) => sum + s.trades, 0);
  const activeSymbols = sessions.map((s) => s.symbol);

  return {
    // State
    sessions,
    isLoading,
    error,
    autoTick,

    // Computed
    totalPnl,
    totalTrades,
    activeSymbols,

    // Actions
    setAutoTick,
    startSession,
    stopSession: (sessionId: string) => stopSessionMutation.mutate(sessionId),
    stopAllSessions: () => stopAllSessionsMutation.mutate(),
    manualTick,
    enterPosition: (sessionId: string, direction: 'long' | 'short', size?: number) =>
      enterPositionMutation.mutate({ sessionId, direction, size }),
    exitPosition: (sessionId: string) => exitPositionMutation.mutate(sessionId),
    refetch,

    // Mutation states
    isCreating: createSessionMutation.isPending,
    isStopping: stopSessionMutation.isPending,
    isStoppingAll: stopAllSessionsMutation.isPending,
    isTicking: tickMutation.isPending,
  };
}
