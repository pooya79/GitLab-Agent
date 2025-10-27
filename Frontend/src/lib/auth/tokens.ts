/**
 * Token management utilities for authentication
 * Handles storing and retrieving tokens from localStorage
 */

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const TOKEN_EXPIRY_KEY = "token_expiry";

export interface AuthTokens {
    accessToken: string;
    refreshToken: string;
    expiresIn: number; // in seconds
}

/**
 * Save authentication tokens to localStorage
 */
export function setAuthTokens(tokens: AuthTokens): void {
    if (typeof window === "undefined") return;

    try {
        localStorage.setItem(ACCESS_TOKEN_KEY, tokens.accessToken);
        localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refreshToken);

        // Calculate expiry timestamp (current time + expires_in seconds)
        const expiryTime = Date.now() + tokens.expiresIn * 1000;
        localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
    } catch (error) {
        console.error("Error saving auth tokens:", error);
    }
}

/**
 * Get the access token from localStorage
 */
export function getAccessToken(): string | null {
    if (typeof window === "undefined") return null;

    try {
        return localStorage.getItem(ACCESS_TOKEN_KEY);
    } catch (error) {
        console.error("Error getting access token:", error);
        return null;
    }
}

/**
 * Get the refresh token from localStorage
 */
export function getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;

    try {
        return localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch (error) {
        console.error("Error getting refresh token:", error);
        return null;
    }
}

/**
 * Get all auth tokens from localStorage
 */
export function getAuthTokens(): AuthTokens | null {
    if (typeof window === "undefined") return null;

    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();
    const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY);

    if (!accessToken || !refreshToken || !expiryTime) {
        return null;
    }

    const expiresIn = Math.max(
        0,
        Math.floor((Number(expiryTime) - Date.now()) / 1000),
    );

    return {
        accessToken,
        refreshToken,
        expiresIn,
    };
}

/**
 * Remove all authentication tokens from localStorage
 */
export function clearAuthTokens(): void {
    if (typeof window === "undefined") return;

    try {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        localStorage.removeItem(TOKEN_EXPIRY_KEY);
    } catch (error) {
        console.error("Error clearing auth tokens:", error);
    }
}

/**
 * Check if the access token is expired or about to expire
 * @param bufferSeconds - Number of seconds before expiry to consider token expired (default: 60)
 */
export function isTokenExpired(bufferSeconds: number = 60): boolean {
    if (typeof window === "undefined") return true;

    try {
        const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY);
        if (!expiryTime) return true;

        const expiryTimestamp = Number(expiryTime);
        const currentTime = Date.now();

        // Consider token expired if it expires within bufferSeconds
        return currentTime >= expiryTimestamp - bufferSeconds * 1000;
    } catch (error) {
        console.error("Error checking token expiry:", error);
        return true;
    }
}

/**
 * Check if user is authenticated (has valid tokens)
 */
export function isAuthenticated(): boolean {
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();

    return !!(accessToken && refreshToken);
}

/**
 * Get the time until token expiry in seconds
 */
export function getTimeUntilExpiry(): number | null {
    if (typeof window === "undefined") return null;

    try {
        const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY);
        if (!expiryTime) return null;

        const expiryTimestamp = Number(expiryTime);
        const currentTime = Date.now();

        return Math.max(0, Math.floor((expiryTimestamp - currentTime) / 1000));
    } catch (error) {
        console.error("Error getting time until expiry:", error);
        return null;
    }
}
