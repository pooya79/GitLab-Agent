"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getAccessTokenApiV1AuthTokenSessionIdGet } from "@/client/sdk.gen";
import { setAuthTokens } from "@/lib/auth";

export default function LoginSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    const redirectTo = searchParams.get("redirect") || "/dashboard";

    if (!sessionId) {
      setError("No session ID provided");
      setIsLoading(false);
      // Redirect to login page after 2 seconds
      setTimeout(() => router.push("/login"), 2000);
      return;
    }

    // Fetch the access token using the session ID
    getAccessTokenApiV1AuthTokenSessionIdGet({
      path: { session_id: sessionId },
    })
      .then((response) => {
        if (response.error) {
          console.error("Error fetching access token:", response.error?.detail);
          setError("Failed to authenticate. Please try again.");
          setIsLoading(false);
          // Redirect to login page after 2 seconds
          setTimeout(() => router.push("/login"), 2000);
          return;
        }

        if (response.data) {
          // Store the tokens using our auth utilities
          setAuthTokens({
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            expiresIn: response.data.expires_in,
          });

          console.log(
            `Authentication successful! Redirecting to ${redirectTo}...`
          );

          // Redirect to the intended page or dashboard
          router.push(redirectTo);
        }
      })
      .catch((error) => {
        console.error("Error fetching access token:", error);
        setError("An unexpected error occurred. Please try again.");
        setIsLoading(false);
        // Redirect to login page after 2 seconds
        setTimeout(() => router.push("/login"), 2000);
      });
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        {isLoading ? (
          <div>
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
            <p className="text-lg">Completing login...</p>
          </div>
        ) : error ? (
          <div>
            <p className="text-lg text-red-600">{error}</p>
            <p className="mt-2 text-sm text-gray-600">Redirecting...</p>
          </div>
        ) : (
          <div>
            <p className="text-lg text-green-600">Login successful!</p>
            <p className="mt-2 text-sm text-gray-600">
              Redirecting to dashboard...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
