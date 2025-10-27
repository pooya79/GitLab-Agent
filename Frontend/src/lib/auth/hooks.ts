/**
 * Custom hooks for authentication
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  isAuthenticated,
  getAccessToken,
  clearAuthTokens,
  setupTokenRefresh,
  ensureValidToken,
} from "./index";

/**
 * Hook to check if user is authenticated
 */
export function useAuth() {
  const [isAuth, setIsAuth] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = isAuthenticated();

      if (authenticated) {
        // Ensure token is valid
        const valid = await ensureValidToken();
        setIsAuth(valid);
      } else {
        setIsAuth(false);
      }

      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const logout = () => {
    clearAuthTokens();
    setIsAuth(false);
    router.push("/login");
  };

  return {
    isAuthenticated: isAuth,
    isLoading,
    logout,
    token: getAccessToken(),
  };
}

/**
 * Hook to set up automatic token refresh
 */
export function useTokenRefresh() {
  const router = useRouter();

  useEffect(() => {
    const cleanup = setupTokenRefresh(
      () => {
        console.log("Token refreshed successfully");
      },
      () => {
        console.error("Token refresh failed, redirecting to login");
        clearAuthTokens();
        router.push("/login");
      }
    );

    return cleanup;
  }, [router]);
}

/**
 * Hook to require authentication
 * Redirects to login if not authenticated
 */
export function useRequireAuth() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      if (!isAuthenticated()) {
        router.push("/login");
        return;
      }

      const valid = await ensureValidToken();
      if (!valid) {
        router.push("/login");
        return;
      }

      setIsChecking(false);
    };

    checkAuth();
  }, [router]);

  return { isChecking };
}
