"use client";

import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    BotsTable,
    type BotsFetchResult,
    type Bot,
    type BotStatus,
} from "@/components/bots-table";

// Mock data for demonstration
const mockBots: Bot[] = [
    {
        id: "1",
        gitlabProject: "my-awesome-project",
        projectUrl: "https://gitlab.com/user/my-awesome-project",
        accessLevel: "Maintainer",
        botName: "Code Review Bot",
        avatar: "/avatars/analyst.png",
        status: "active",
        hasBot: true,
    },
    {
        id: "2",
        gitlabProject: "backend-api",
        projectUrl: "https://gitlab.com/user/backend-api",
        accessLevel: "Owner",
        botName: "DevOps Assistant",
        avatar: "/avatars/cyber_samurai.png",
        status: "active",
        hasBot: true,
    },
    {
        id: "3",
        gitlabProject: "frontend-app",
        projectUrl: "https://gitlab.com/user/frontend-app",
        accessLevel: "Developer",
        botName: "CI/CD Helper",
        avatar: "/avatars/hacker.png",
        status: "stopped",
        hasBot: true,
    },
    {
        id: "4",
        gitlabProject: "data-pipeline",
        projectUrl: "https://gitlab.com/user/data-pipeline",
        accessLevel: "Maintainer",
        botName: "Analytics Bot",
        avatar: "/avatars/librarian.png",
        status: "error",
        errorMessage:
            "Failed to connect to GitLab API. Please check your access token.",
        hasBot: true,
    },
    {
        id: "5",
        gitlabProject: "mobile-app",
        projectUrl: "https://gitlab.com/user/mobile-app",
        accessLevel: "Owner",
        hasBot: false,
    },
    {
        id: "6",
        gitlabProject: "infrastructure",
        projectUrl: "https://gitlab.com/user/infrastructure",
        accessLevel: "Developer",
        hasBot: false,
    },
];

export default function DashboardPage() {
    // Mock fetch function - replace with actual API call
    const fetchBots = async (
        page: number,
        perPage: number,
    ): Promise<BotsFetchResult> => {
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Calculate pagination
        const startIndex = (page - 1) * perPage;
        const endIndex = startIndex + perPage;
        const items = mockBots.slice(startIndex, endIndex);

        return {
            items,
            total: mockBots.length,
        };

        // Example with real API call:
        // const response = await fetch(`/api/v1/bots?page=${page}&per_page=${perPage}`);
        // const data = await response.json();
        // return {
        //     items: data.items,
        //     total: data.total,
        // };
    };

    // Mock fetch bot status function - replace with actual API call
    const fetchBotStatus = async (botId: string): Promise<BotStatus> => {
        // Simulate API delay
        await new Promise((resolve) => setTimeout(resolve, 1000));

        // Return mock status based on bot data
        const bot = mockBots.find((b) => b.id === botId);
        if (!bot || !bot.hasBot) {
            throw new Error("Bot not found");
        }

        return {
            status: bot.status || "active",
            errorMessage: bot.errorMessage,
        };

        // Example with real API call:
        // const response = await fetch(`/api/v1/bots/${botId}/status`);
        // const data = await response.json();
        // return {
        //     status: data.status,
        //     errorMessage: data.error_message,
        // };
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                <p className="text-muted-foreground">
                    Welcome to your GitLab Agent dashboard
                </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card>
                    <CardHeader>
                        <CardTitle>Projects</CardTitle>
                        <CardDescription>
                            Connected GitLab projects
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">3</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Webhooks</CardTitle>
                        <CardDescription>
                            Active webhook listeners
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">5</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Bots</CardTitle>
                        <CardDescription>AI bots configured</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p className="text-3xl font-bold">3</p>
                    </CardContent>
                </Card>
            </div>

            {/* Bots Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Active Bots</CardTitle>
                    <CardDescription>
                        Manage your GitLab bots and their configurations
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <BotsTable
                        fetchBots={fetchBots}
                        fetchBotStatus={fetchBotStatus}
                    />
                </CardContent>
            </Card>
        </div>
    );
}
