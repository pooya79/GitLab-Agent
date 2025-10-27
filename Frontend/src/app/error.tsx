"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Home, RefreshCw } from "lucide-react";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    const router = useRouter();

    useEffect(() => {
        // Log the error to an error reporting service
        console.error(error);
    }, [error]);

    return (
        <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-zinc-50 to-zinc-100 p-4 font-sans dark:from-zinc-950 dark:to-black">
            <Card className="w-full max-w-md border-zinc-200 shadow-xl dark:border-zinc-800">
                <CardContent className="pt-8 pb-6">
                    <div className="text-center">
                        {/* Error Icon */}
                        <div className="mb-6">
                            <div className="mx-auto w-20 h-20 bg-red-100 dark:bg-red-950 rounded-full flex items-center justify-center mb-4">
                                <svg
                                    className="w-10 h-10 text-red-600 dark:text-red-400"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                    />
                                </svg>
                            </div>
                            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
                                Oops! Something went wrong
                            </h1>
                            <div className="mt-2 h-1 w-24 bg-linear-to-r from-red-500 to-orange-600 mx-auto rounded-full"></div>
                        </div>

                        {/* Error Message */}
                        <div className="mb-8">
                            <p className="text-zinc-600 dark:text-zinc-400 mb-2">
                                We encountered an unexpected error. Please try
                                again.
                            </p>
                            {error.digest && (
                                <p className="text-xs text-zinc-500 dark:text-zinc-500 font-mono">
                                    Error ID: {error.digest}
                                </p>
                            )}
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-col sm:flex-row gap-3 justify-center">
                            <Button
                                onClick={() => reset()}
                                variant="outline"
                                className="gap-2"
                            >
                                <RefreshCw className="h-4 w-4" />
                                Try Again
                            </Button>
                            <Button
                                onClick={() => router.push("/dashboard")}
                                className="gap-2 bg-linear-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                            >
                                <Home className="h-4 w-4" />
                                Go to Dashboard
                            </Button>
                        </div>

                        {/* Additional Help Text */}
                        <p className="mt-6 text-sm text-zinc-500 dark:text-zinc-500">
                            If this problem persists, please contact support.
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
