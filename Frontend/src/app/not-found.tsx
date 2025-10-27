"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Home, ArrowLeft } from "lucide-react";

export default function NotFound() {
    const router = useRouter();

    return (
        <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-zinc-50 to-zinc-100 p-4 font-sans dark:from-zinc-950 dark:to-black">
            <Card className="w-full max-w-md border-zinc-200 shadow-xl dark:border-zinc-800">
                <CardContent className="pt-8 pb-6">
                    <div className="text-center">
                        {/* 404 Error Code */}
                        <div className="mb-6">
                            <h1 className="text-8xl font-bold text-zinc-900 dark:text-zinc-100">
                                404
                            </h1>
                            <div className="mt-2 h-1 w-24 bg-linear-to-r from-blue-500 to-purple-600 mx-auto rounded-full"></div>
                        </div>

                        {/* Error Message */}
                        <div className="mb-8">
                            <h2 className="text-2xl font-semibold text-zinc-800 dark:text-zinc-200 mb-2">
                                Page Not Found
                            </h2>
                            <p className="text-zinc-600 dark:text-zinc-400">
                                Sorry, the page you're looking for doesn't exist
                                or has been moved.
                            </p>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-col sm:flex-row gap-3 justify-center">
                            <Button
                                onClick={() => router.back()}
                                variant="outline"
                                className="gap-2"
                            >
                                <ArrowLeft className="h-4 w-4" />
                                Go Back
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
                            If you believe this is an error, please contact
                            support.
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
