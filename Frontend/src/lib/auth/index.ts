/**
 * Auth utilities index
 * Exports all authentication-related functions
 */

export {
    setAuthTokens,
    getAccessToken,
    getRefreshToken,
    getAuthTokens,
    clearAuthTokens,
    isTokenExpired,
    isAuthenticated,
    getTimeUntilExpiry,
    type AuthTokens,
} from "./tokens";

export {
    refreshAccessToken,
    ensureValidToken,
    setupTokenRefresh,
} from "./refresh";

export { ProtectedRoute, withAuth } from "./protected";

export { useAuth, useTokenRefresh, useRequireAuth } from "./hooks";

export { AuthProvider } from "./provider";

export {
    getAuthHeaders,
    authenticatedFetch,
    authenticatedFetchJSON,
} from "./api";
