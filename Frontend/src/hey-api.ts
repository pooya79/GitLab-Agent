import type { CreateClientConfig } from "@/client/client.gen";
import { env } from "@/env";

export const createClientConfig: CreateClientConfig = (config) => ({
    ...config,
    baseUrl: env.BACKEND_URL,
});
