/**
 * Token refresh utilities
 * Handles automatic token refresh when expired
 */

import { refreshTokenApiV1AuthRefreshPost } from "@/client/sdk.gen";
import {
  getRefreshToken,
  setAuthTokens,
  clearAuthTokens,
  isTokenExpired,
} from "./tokens";

let refreshPromise: Promise<boolean> | null = null;

/**
 * Refresh the access token using the refresh token
 * @returns Promise<boolean> - true if refresh was successful, false otherwise
 */
export async function refreshAccessToken(): Promise<boolean> {
  // If a refresh is already in progress, return the existing promise
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const refreshToken = getRefreshToken();

      if (!refreshToken) {
        console.error("No refresh token available");
        clearAuthTokens();
        return false;
      }

      const response = await refreshTokenApiV1AuthRefreshPost({
        body: {
          refresh_token: refreshToken,
        },
      });

      if (response.error) {
        console.error("Error refreshing token:", response.error);
        clearAuthTokens();
        return false;
      }

      if (response.data) {
        // Store the new tokens
        setAuthTokens({
          accessToken: response.data.access_token,
          refreshToken: response.data.refresh_token,
          expiresIn: response.data.expires_in,
        });

        console.log("Token refreshed successfully");
        return true;
      }

      return false;
    } catch (error) {
      console.error("Exception while refreshing token:", error);
      clearAuthTokens();
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

/**
 * Ensure the access token is valid, refreshing if necessary
 * @returns Promise<boolean> - true if token is valid or was successfully refreshed
 */
export async function ensureValidToken(): Promise<boolean> {
  if (!isTokenExpired()) {
    return true;
  }

  console.log("Token expired or about to expire, refreshing...");
  return await refreshAccessToken();
}

/**
 * Set up automatic token refresh
 * @param onTokenRefreshed - Optional callback when token is refreshed
 * @param onRefreshFailed - Optional callback when token refresh fails
 * @returns Function to clear the interval
 */
export function setupTokenRefresh(
  onTokenRefreshed?: () => void,
  onRefreshFailed?: () => void
): () => void {
  // Check token expiry every minute
  const intervalId = setInterval(async () => {
    if (isTokenExpired(300)) {
      // Refresh 5 minutes before expiry
      const success = await refreshAccessToken();

      if (success && onTokenRefreshed) {
        onTokenRefreshed();
      } else if (!success && onRefreshFailed) {
        onRefreshFailed();
      }
    }
  }, 60000); // Check every minute

  // Return cleanup function
  return () => clearInterval(intervalId);
}
