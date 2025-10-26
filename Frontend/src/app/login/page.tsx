"use client";

import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { gitlabLoginApiV1AuthGitlabLoginGet } from "@/client/sdk.gen";

export default function LoginPage() {
    const handleGitlabSignIn = async () => {
        console.log("GitLab sign-in initiated");
        const { data, error } = await gitlabLoginApiV1AuthGitlabLoginGet();
        console.log("Redirecting to GitLab for authentication...");
        if (error) {
            console.error("Error during GitLab login:", error);
            return;
        }
        if (data && data.url) {
            window.location.href = data.url;
        } else {
            console.error("No URL received for GitLab login");
        }
    };

    return (
        <div className="flex h-screen items-center justify-center">
            <Card className="w-[360px] p-4 text-center shadow-md">
                <CardHeader>
                    <CardTitle className="text-xl font-semibold">
                        Sign in
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Button
                        className="w-full flex items-center justify-center gap-2 cursor-pointer"
                        onClick={handleGitlabSignIn}
                    >
                        <svg
                            role="img"
                            viewBox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-5 w-5 text-[#fc6d26]"
                            fill="currentColor"
                        >
                            <title>GitLab</title>
                            <path d="m23.6004 9.5927-.0337-.0862L20.3.9814a.851.851 0 0 0-.3362-.405.8748.8748 0 0 0-.9997.0539.8748.8748 0 0 0-.29.4399l-2.2055 6.748H7.5375l-2.2057-6.748a.8573.8573 0 0 0-.29-.4412.8748.8748 0 0 0-.9997-.0537.8585.8585 0 0 0-.3362.4049L.4332 9.5015l-.0325.0862a6.0657 6.0657 0 0 0 2.0119 7.0105l.0113.0087.03.0213 4.976 3.7264 2.462 1.8633 1.4995 1.1321a1.0085 1.0085 0 0 0 1.2197 0l1.4995-1.1321 2.4619-1.8633 5.006-3.7489.0125-.01a6.0682 6.0682 0 0 0 2.0094-7.003z" />
                        </svg>
                        Sign in with GitLab
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
