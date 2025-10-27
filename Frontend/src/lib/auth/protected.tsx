/**
 * Protected route wrapper
 * Checks if user is authenticated and redirects to login if not
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { isAuthenticated, ensureValidToken } from "./index";

interface ProtectedRouteProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

/**
 * Wrapper component for protected routes
 * Redirects to login if user is not authenticated
 */
export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [isChecking, setIsChecking] = useState(true);
    const [isAuthorized, setIsAuthorized] = useState(false);

    useEffect(() => {
        const checkAuth = async () => {
            // Check if user has tokens
            if (!isAuthenticated()) {
                console.log("User not authenticated, redirecting to login...");
                router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
                return;
            }

            // Ensure token is valid (refresh if needed)
            const isValid = await ensureValidToken();

            if (!isValid) {
                console.log("Token validation failed, redirecting to login...");
                router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
                return;
            }

            setIsAuthorized(true);
            setIsChecking(false);
        };

        checkAuth();
    }, [router, pathname]);

    // Show loading state while checking authentication
    if (isChecking) {
        return (
            fallback || (
                <div className="flex min-h-screen items-center justify-center">
                    <div className="text-center">
                        <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
                        <p className="text-lg">Loading...</p>
                    </div>
                </div>
            )
        );
    }

    // Only render children if authorized
    return isAuthorized ? <>{children}</> : null;
}

/**
 * HOC to wrap page components with authentication
 */
export function withAuth<P extends object>(
    Component: React.ComponentType<P>,
    fallback?: React.ReactNode,
) {
    return function ProtectedComponent(props: P) {
        return (
            <ProtectedRoute fallback={fallback}>
                <Component {...props} />
            </ProtectedRoute>
        );
    };
}
