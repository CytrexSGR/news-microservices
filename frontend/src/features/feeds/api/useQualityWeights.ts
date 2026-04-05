/**
 * React Query hooks for Quality Score Weights API
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { feedApi } from '@/api/axios';
import type { QualityWeight, QualityWeightUpdate, WeightValidation, ConfigurationStatus } from '../types/admiraltyCode';

/**
 * Get all quality score weights
 */
export const useQualityWeights = () => {
  return useQuery<QualityWeight[]>({
    queryKey: ['admiralty-codes', 'weights'],
    queryFn: async () => {
      const { data } = await feedApi.get('/admiralty-codes/weights');
      return data;
    },
  });
};

/**
 * Get a specific weight by category
 */
export const useQualityWeight = (category: string) => {
  return useQuery<QualityWeight>({
    queryKey: ['admiralty-codes', 'weights', category],
    queryFn: async () => {
      const { data } = await feedApi.get(`/admiralty-codes/weights/${category}`);
      return data;
    },
    enabled: !!category,
  });
};

/**
 * Update a weight
 */
export const useUpdateQualityWeight = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ category, updates }: { category: string; updates: QualityWeightUpdate }) => {
      const { data } = await feedApi.put(`/admiralty-codes/weights/${category}`, updates);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admiralty-codes', 'weights'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] }); // Refresh feeds to show updated scores
    },
  });
};

/**
 * Reset all weights to defaults
 */
export const useResetQualityWeights = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data } = await feedApi.post('/admiralty-codes/weights/reset');
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admiralty-codes', 'weights'] });
      queryClient.invalidateQueries({ queryKey: ['feeds'] });
    },
  });
};

/**
 * Validate that weights sum to 1.00
 */
export const useValidateWeights = () => {
  return useQuery<WeightValidation>({
    queryKey: ['admiralty-codes', 'weights', 'validate'],
    queryFn: async () => {
      const { data } = await feedApi.get('/admiralty-codes/weights/validate');
      return data;
    },
  });
};

/**
 * Get overall configuration status
 */
export const useConfigurationStatus = () => {
  return useQuery<ConfigurationStatus>({
    queryKey: ['admiralty-codes', 'status'],
    queryFn: async () => {
      const { data } = await feedApi.get('/admiralty-codes/status');
      return data;
    },
  });
};
