/**
 * Authenticated API utilities
 * Helper functions for making API calls with automatic token handling
 */

import { getAccessToken, ensureValidToken } from "./index";

/**
 * Get authorization headers with the current access token
 */
export async function getAuthHeaders(): Promise<HeadersInit> {
  await ensureValidToken();
  const token = getAccessToken();

  if (!token) {
    throw new Error("No access token available");
  }

  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

/**
 * Make an authenticated fetch request
 * Automatically includes the access token in headers
 */
export async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const authHeaders = await getAuthHeaders();

  return fetch(url, {
    ...options,
    headers: {
      ...authHeaders,
      ...options.headers,
    },
  });
}

/**
 * Example usage with JSON response
 */
export async function authenticatedFetchJSON<T = any>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await authenticatedFetch(url, options);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} - ${error}`);
  }

  return response.json();
}
