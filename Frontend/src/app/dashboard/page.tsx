"use client";

import { useState, useCallback } from "react";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { BotsTable, type Bot, type BotStatus } from "@/components/bots-table";
import { CreateBotDialog } from "@/components/create-bot-dialog";
import {
    listGitlabProjectsApiV1GitlabProjectsGet,
    getBotStatusApiV1BotsBotIdStatusGet,
    createBotApiV1BotsPost,
    toggleBotActiveApiV1BotsBotIdToggleActivePatch,
    createNewBotAccessTokenApiV1BotsBotIdNewAccessTokenPatch,
    deleteBotApiV1BotsBotIdDelete,
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
        async (
            page: number,
            perPage: number,
            search?: string,
        ): Promise<Bot[]> => {
            try {
                const searchTerm = search?.trim();
                const query: {
                    page: number;
                    per_page: number;
                    search?: string;
                } = {
                    page,
                    per_page: perPage,
                };

                if (searchTerm) {
                    query.search = searchTerm;
                }

                const response = await listGitlabProjectsApiV1GitlabProjectsGet(
                    {
                        query,
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

                const rawProjects = Array.isArray(response.data)
                    ? response.data
                    : [];

                return rawProjects.map((project: any) => {
                    return {
                        gitlabProjectId: project.id,
                        gitlabProject: project.name_with_namespace,
                        gitlabProjectPathName: project.path_with_namespace,
                        projectUrl: project.web_url,
                        accessLevel: ACCESS_LEVEL[project.access_level],
                        botId: project.bot_id ?? undefined,
                        botName: project.bot_name ?? undefined,
                        avatar: project.avatar_url ?? undefined,
                        hasBot: Boolean(project.bot_id),
                    } as Bot;
                });
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
                // Check if it's a 404 (bot not found - likely deleted)
                if (response.response.status === 404) {
                    throw new Error(
                        `Bot ${botId} not found (may have been deleted)`,
                    );
                }
                throw new Error(
                    `Failed to fetch bot status: ${response.error}`,
                );
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

    // Mock handler for stopping/starting bot
    const handleStopBot = async (botId: number, botName: string) => {
        try {
            console.log(`Toggling bot status for: ${botName} (ID: ${botId})`);

            const response =
                await toggleBotActiveApiV1BotsBotIdToggleActivePatch({
                    path: { bot_id: botId },
                });

            if (response.error) {
                throw new Error("Wrong input type.");
            }

            if (response.response.status !== 200) {
                throw new Error(
                    `Failed to toggle bot status: ${response.response.statusText}`,
                );
            }

            const isActive = response.data.is_active;
            alert(
                `Bot "${botName}" is now ${isActive ? "active" : "inactive"}.`,
            );

            // Refresh the table to show updated status
            setRefreshTrigger((prev) => prev + 1);
        } catch (error) {
            console.error(`Error toggling bot status for ${botName}:`, error);
            alert(
                `Failed to toggle bot status: ${
                    error instanceof Error ? error.message : "Unknown error"
                }`,
            );
        }
    };

    // Mock handler for creating new token
    const handleCreateNewToken = async (botId: number, botName: string) => {
        try {
            console.log(`Creating new token for: ${botName} (ID: ${botId})`);

            const response =
                await createNewBotAccessTokenApiV1BotsBotIdNewAccessTokenPatch({
                    path: { bot_id: botId },
                });

            if (response.error) {
                throw new Error("Wrong input type.");
            }

            if (response.response.status !== 200) {
                throw new Error(
                    `Failed to create new token: ${response.response.statusText}`,
                );
            }

            if (response.data.warning) {
                alert(
                    `New token created for "${botName}"! The old token has been invalidated.\nWarning: ${response.data.warning}`,
                );
            } else {
                alert(
                    `New token created for "${botName}"! The old token has been invalidated.`,
                );
            }

            // Refresh the table
            setRefreshTrigger((prev) => prev + 1);
        } catch (error) {
            console.error(`Error creating new token for ${botName}:`, error);
            alert(
                `Failed to create new token: ${
                    error instanceof Error ? error.message : "Unknown error"
                }`,
            );
        }
    };

    // Mock handler for removing bot
    const handleRemoveBot = async (botId: number, botName: string) => {
        try {
            console.log(`Removing bot: ${botName} (ID: ${botId})`);
            const response = await deleteBotApiV1BotsBotIdDelete({
                path: { bot_id: botId },
            });

            if (response.error) {
                throw new Error(`Wrong input type.`);
            }

            if (response.response.status !== 200) {
                throw new Error(
                    `Failed to remove bot: ${response.response.statusText}`,
                );
            }

            if (response.data.warning) {
                alert(
                    `Bot "${botName}" removed successfully! Warning: ${response.data.warning}`,
                );
            } else {
                alert(`Bot "${botName}" removed successfully!`);
            }

            // Refresh the table to remove the deleted bot
            setRefreshTrigger((prev) => prev + 1);
        } catch (error) {
            console.error(`Error removing bot ${botName}:`, error);
            alert(
                `Failed to remove bot: ${
                    error instanceof Error ? error.message : "Unknown error"
                }`,
            );
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
                        <CardTitle>Bots</CardTitle>
                        <CardDescription>AI bots configured</CardDescription>
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
                    <CardTitle>Bots</CardTitle>
                    <CardDescription>
                        Manage your GitLab bots and their configurations
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <BotsTable
                        fetchBots={fetchBots}
                        fetchBotStatus={fetchBotStatus}
                        onCreateBot={handleOpenCreateDialog}
                        onStopBot={handleStopBot}
                        onCreateNewToken={handleCreateNewToken}
                        onRemoveBot={handleRemoveBot}
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
