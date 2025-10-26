"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getAccessTokenApiV1AuthTokenSessionIdGet } from "@/client/sdk.gen";

export default function LoginSuccessPage() {
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => {
        const sessionId = searchParams.get("session_id");
        console.log(sessionId);

        if (sessionId) {
            getAccessTokenApiV1AuthTokenSessionIdGet({
                path: { session_id: sessionId },
            })
                .then((response) => {
                    // Handle successful response
                    console.log("Access Token Response:", response);
                })
                .catch((error) => {
                    // Handle error
                    console.error("Error fetching access token:", error);
                });
        }
    }, []);
}
