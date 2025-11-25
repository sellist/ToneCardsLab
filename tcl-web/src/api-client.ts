/**
 * Example API client using the generated TypeScript types
 *
 * This demonstrates how to use the generated types from OpenAPI spec
 */

import type { components } from './types/api';

// Type aliases for convenience
type HealthCheckResponse = components['schemas']['HealthCheckResponse'];

const API_BASE_URL = 'http://localhost:8000';

async function fetchAPI<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  async healthCheck(): Promise<HealthCheckResponse> {
    return fetchAPI<HealthCheckResponse>('/api/v1/health');
  },
};
