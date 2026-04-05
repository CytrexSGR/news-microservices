/**
 * React Query hooks for Admiralty Code Thresholds API
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { AdmiraltyThreshold, AdmiraltyThresholdUpdate } from '../types/admiraltyCode';

/**
 * Get all admiralty code thresholds
 */
export const useAdmiraltyThresholds = () => {
  return useQuery<AdmiraltyThreshold[]>({
    queryKey: ['admiralty-codes', 'thresholds'],
    queryFn: async () => {
      const { data } = await feedApi.get('/admiralty-codes/thresholds');
      return data;
    },
  });
};

/**
 * Get a specific threshold by code
 */
export const useAdmiraltyThreshold = (code: string) => {
  return useQuery<AdmiraltyThreshold>({
    queryKey: ['admiralty-codes', 'thresholds', code],
    queryFn: async () => {
      const { data } = await feedApi.get(`/admiralty-codes/thresholds/${code}`);
      return data;
    },
    enabled: !!code,
  });
};

/**
 * Update a threshold
 */
export const useUpdateAdmiraltyThreshold = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ code, updates }: { code: string; updates: AdmiraltyThresholdUpdate }) => {
      const { data } = await feedApi.put(`/admiralty-codes/thresholds/${code}`, updates);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admiralty-codes', 'thresholds'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] }); // Refresh feeds to show updated codes
    },
  });
};

/**
 * Reset all thresholds to defaults
 */
export const useResetAdmiraltyThresholds = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data } = await feedApi.post('/admiralty-codes/thresholds/reset');
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admiralty-codes', 'thresholds'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
};
