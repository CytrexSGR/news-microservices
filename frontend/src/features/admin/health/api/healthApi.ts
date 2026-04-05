/**
 * Health API Client
 *
 * API client for the analytics-service health monitoring endpoints.
 * Uses dynamic hostname for LAN access support.
 */

import type {
  HealthSummary,
  ContainerHealth,
  HealthAlert,
} from '../types/health';

/**
 * Get the base URL for the analytics service health API.
 * Uses current hostname for LAN access support.
 */
const getBaseUrl = (): string => {
  const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  return `http://${hostname}:8107/api/v1/health`;
};

/**
 * Fetch health summary statistics
 */
export async function fetchHealthSummary(): Promise<HealthSummary> {
  const response = await fetch(`${getBaseUrl()}/summary`);
  if (!response.ok) {
    throw new Error(`Failed to fetch health summary: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch container health status
 */
export async function fetchContainerHealth(): Promise<ContainerHealth[]> {
  const response = await fetch(`${getBaseUrl()}/containers`);
  if (!response.ok) {
    throw new Error(`Failed to fetch container health: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch health alerts
 */
export async function fetchHealthAlerts(limit: number = 20): Promise<HealthAlert[]> {
  const response = await fetch(`${getBaseUrl()}/alerts?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch health alerts: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch all health data in parallel
 */
export async function fetchAllHealthData(): Promise<{
  summary: HealthSummary;
  containers: ContainerHealth[];
  alerts: HealthAlert[];
}> {
  const [summary, containers, alerts] = await Promise.all([
    fetchHealthSummary(),
    fetchContainerHealth(),
    fetchHealthAlerts(),
  ]);

  return { summary, containers, alerts };
}
