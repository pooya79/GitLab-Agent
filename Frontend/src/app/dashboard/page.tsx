"use client";

import { useState, useCallback } from "react";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
    BotsTable,
    type BotsFetchResult,
    type Bot,
    type BotStatus,
} from "@/components/bots-table";
import { CreateBotDialog } from "@/components/create-bot-dialog";
import {
    listGitlabProjectsApiV1GitlabProjectsGet,
    getBotStatusApiV1BotsBotIdStatusGet,
    createBotApiV1BotsPost,
} from "@/client/sdk.gen";

const ACCESS_LEVEL: Record<number, string> = {
    10: "Guest",
    20: "Reporter",
    30: "Developer",
    40: "Maintainer",
    50: "Owner",
};

export default function DashboardPage() {
    const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
    const [selectedProjectPathName, setSelectedProjectPathName] = useState<
        string | null
    >(null);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    const handleOpenCreateDialog = (projectPathName: string) => {
        setSelectedProjectPathName(projectPathName);
        setIsCreateDialogOpen(true);
    };

    const handleCreateBot = async (botName: string, projectPath: string) => {
        const response = await createBotApiV1BotsPost({
            body: {
                name: botName,
                gitlab_project_path: projectPath,
            },
        });

        if (response.error) {
            throw new Error("Failed to create bot");
        }

        if (response.response.status !== 201) {
            throw new Error(
                `Failed to create bot: ${response.response.statusText}`,
            );
        }

        // Success - refresh the table
        setRefreshTrigger((prev) => prev + 1);
    };

    // Fetch bots from API
    const fetchBots = useCallback(
        async (page: number, perPage: number): Promise<BotsFetchResult> => {
            try {
                const response = await listGitlabProjectsApiV1GitlabProjectsGet(
                    {
                        query: { page, per_page: perPage },
                    },
                );

                if (response.error) {
                    throw new Error("Wrong input type.");
                }

                if (response.response.status !== 200) {
                    throw new Error(
                        `Failed to fetch bots: ${response.response.statusText}`,
                    );
                }
                const total: number = response.data.total;
                const items: Bot[] = response.data.projects.map(
                    (project: any) => {
                        return {
                            gitlabProjectId: project.id,
                            gitlabProject: project.name_with_namespace,
                            gitlabProjectPathName: project.path_with_namespace,
                            projectUrl: project.web_url,
                            accessLevel: ACCESS_LEVEL[project.access_level],
                            botId: project.bot_id ?? undefined,
                            botName: project.bot_name ?? undefined,
                            avatar: project.avatar_url ?? undefined,
                            hasBot: project.bot_id ? true : false,
                        } as Bot;
                    },
                );
                return { total, items };
            } catch (error) {
                console.error("Error fetching bots:", error);
                throw error instanceof Error
                    ? error
                    : new Error("Unknown error while fetching bots");
            }
        },
        [refreshTrigger],
    );

    // Fetch bot status from API
    const fetchBotStatus = async (botId: number): Promise<BotStatus> => {
        try {
            const response = await getBotStatusApiV1BotsBotIdStatusGet({
                path: { bot_id: botId },
            });

            if (response.error) {
                throw new Error("Wrong input type.");
            }

            if (response.response.status !== 200) {
                throw new Error(
                    `Failed to fetch bot status: ${response.response.statusText}`,
                );
            }
            return {
                status: response.data.status,
                errorMessage: response.data.error_message ?? undefined,
            };
        } catch (error) {
            console.error(`Error fetching status for bot ${botId}:`, error);
            throw error instanceof Error
                ? error
                : new Error("Unknown error while fetching bot status");
        }
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
                        onCreateBot={handleOpenCreateDialog}
                    />
                </CardContent>
            </Card>

            {/* Create Bot Dialog */}
            <CreateBotDialog
                isOpen={isCreateDialogOpen}
                onOpenChange={setIsCreateDialogOpen}
                projectPathName={selectedProjectPathName}
                onCreateBot={handleCreateBot}
            />
        </div>
    );
}
