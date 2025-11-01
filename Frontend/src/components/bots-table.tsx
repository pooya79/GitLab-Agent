"use client";

import { useState, useEffect } from "react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import Link from "next/link";
import {
    MoreVertical,
    BarChart3,
    Settings,
    ChevronFirst,
    ChevronLast,
    ChevronLeft,
    ChevronRight,
    CheckCircle2,
    XCircle,
    Pause,
    StopCircle,
    Play,
    KeyRound,
    Trash2,
    AlertCircle,
} from "lucide-react";

type StatusLiterals = "ACTIVE" | "STOPPED" | "ERROR";

// Types
export interface Bot {
    gitlabProjectId: number;
    gitlabProject: string;
    gitlabProjectPathName: string;
    projectUrl: string;
    accessLevel: "Owner" | "Maintainer" | "Developer" | "Reporter" | "Guest";
    botId?: number; // Optional - null if no bot configured
    botName?: string; // Optional - null if no bot configured
    avatar?: string; // Optional - null if no bot configured
    status?: StatusLiterals; // Optional - null if no bot configured
    errorMessage?: string;
    hasBot: boolean; // Indicates if project has a bot configured
}

export interface BotsFetchResult {
    items: Bot[];
    total: number;
}

export interface BotStatus {
    status: StatusLiterals;
    errorMessage?: string;
}

interface BotsTableProps {
    fetchBots: (page: number, perPage: number) => Promise<BotsFetchResult>;
    fetchBotStatus?: (botId: number) => Promise<BotStatus>;
    onCreateBot?: (projectPathName: string) => void;
}

export function BotsTable({
    fetchBots,
    fetchBotStatus,
    onCreateBot,
}: BotsTableProps) {
    const [currentPage, setCurrentPage] = useState(1);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [bots, setBots] = useState<Bot[]>([]);
    const [totalBots, setTotalBots] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [botStatuses, setBotStatuses] = useState<Map<number, BotStatus>>(
        new Map(),
    );
    const [loadingStatuses, setLoadingStatuses] = useState<Set<number>>(
        new Set(),
    );

    // Fetch bots whenever page or rowsPerPage changes
    useEffect(() => {
        const loadBots = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const result = await fetchBots(currentPage, rowsPerPage);
                setBots(result.items);
                setTotalBots(result.total);
            } catch (err) {
                setError(
                    err instanceof Error ? err.message : "Failed to fetch bots",
                );
                console.error("Error fetching bots:", err);
            } finally {
                setIsLoading(false);
            }
        };

        loadBots();
    }, [currentPage, rowsPerPage, fetchBots]);

    // Fetch statuses for bots that have a bot configured
    useEffect(() => {
        if (!fetchBotStatus || bots.length === 0) return;

        const loadBotStatuses = async () => {
            // Mark all bot IDs as loading
            const botsWithBots = bots.filter((bot) => bot.hasBot);
            const loadingIds = new Set(botsWithBots.map((bot) => bot.botId!));
            setLoadingStatuses(loadingIds);

            // Fetch statuses for all bots that have a bot configured
            const statusPromises = botsWithBots.map(async (bot) => {
                try {
                    const status = await fetchBotStatus(bot.botId!);
                    // Update status immediately as it's fetched
                    setBotStatuses((prev) => {
                        const newMap = new Map(prev);
                        newMap.set(bot.botId!, status);
                        return newMap;
                    });
                    // Remove from loading set
                    setLoadingStatuses((prev) => {
                        const newSet = new Set(prev);
                        newSet.delete(bot.botId!);
                        return newSet;
                    });
                } catch (err) {
                    console.error(
                        `Failed to fetch status for bot ID: ${bot.botId}:`,
                        err,
                    );
                    // Set error status if fetch fails
                    setBotStatuses((prev) => {
                        const newMap = new Map(prev);
                        newMap.set(bot.botId!, {
                            status: "ERROR",
                            errorMessage: "Failed to fetch bot status",
                        });
                        return newMap;
                    });
                    // Remove from loading set
                    setLoadingStatuses((prev) => {
                        const newSet = new Set(prev);
                        newSet.delete(bot.botId!);
                        return newSet;
                    });
                }
            });

            await Promise.all(statusPromises);
        };

        loadBotStatuses();
    }, [bots, fetchBotStatus]);

    // Calculate pagination
    const totalPages = Math.ceil(totalBots / rowsPerPage);

    // Get the current status for a bot (prioritize fetched status over initial data)
    const getBotStatus = (
        bot: Bot,
    ): { status: Bot["status"]; errorMessage?: string; isLoading: boolean } => {
        if (bot.hasBot && bot.botId) {
            // Check if status is currently being loaded
            if (fetchBotStatus && loadingStatuses.has(bot.botId)) {
                return {
                    status: undefined,
                    isLoading: true,
                };
            }

            // Check if we have a fetched status
            if (botStatuses.has(bot.botId)) {
                const fetchedStatus = botStatuses.get(bot.botId)!;
                return {
                    status: fetchedStatus.status,
                    errorMessage: fetchedStatus.errorMessage,
                    isLoading: false,
                };
            }
        }

        // Return initial status from bot data
        return {
            status: bot.status,
            errorMessage: bot.errorMessage,
            isLoading: false,
        };
    };

    const handleRemoveBot = (botId: number, botName: string) => {
        if (confirm(`Are you sure you want to remove "${botName}"?`)) {
            console.log("Removing bot:", botId);
            // Add your remove logic here
        }
    };

    const handleStopBot = (botId: number, botName: string) => {
        console.log("Stopping bot:", botId, botName);
        // Add your stop logic here
    };

    const handleRevokeToken = (botId: number, botName: string) => {
        if (
            confirm(
                `Are you sure you want to revoke the token for "${botName}"?`,
            )
        ) {
            console.log("Revoking token for bot:", botId);
            // Add your revoke logic here
        }
    };

    const getStatusBadge = (status: Bot["status"], errorMessage?: string) => {
        switch (status) {
            case "ACTIVE":
                return (
                    <Badge
                        variant="default"
                        className="bg-green-600 hover:bg-green-700"
                    >
                        <CheckCircle2 className="h-3 w-3" />
                        Active
                    </Badge>
                );
            case "STOPPED":
                return (
                    <Badge variant="secondary">
                        <Pause className="h-3 w-3" />
                        Stopped
                    </Badge>
                );
            case "ERROR":
                return (
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Badge
                                    variant="destructive"
                                    className="cursor-help"
                                >
                                    <XCircle className="h-3 w-3" />
                                    Error
                                </Badge>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs">
                                <p>
                                    {errorMessage ||
                                        "An error occurred with this bot"}
                                </p>
                            </TooltipContent>
                        </Tooltip>
                    </TooltipProvider>
                );
            default:
                return (
                    <Badge variant="outline">
                        <AlertCircle className="h-3 w-3" />
                        {status}
                    </Badge>
                );
        }
    };

    const getAccessLevelBadge = (level: Bot["accessLevel"]) => {
        const variants = {
            Owner: "default",
            Maintainer: "secondary",
            Developer: "outline",
            Reporter: "outline",
            Guest: "outline",
        } as const;

        return <Badge variant={variants[level]}>{level}</Badge>;
    };

    return (
        <div className="space-y-4">
            {/* Table */}
            <div className="rounded-md border overflow-hidden">
                <div className="overflow-x-auto custom-scrollbar">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Bot</TableHead>
                                <TableHead>GitLab Project</TableHead>
                                <TableHead>Access Level</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Links</TableHead>
                                <TableHead className="text-right">
                                    Actions
                                </TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow key="loading">
                                    <TableCell
                                        colSpan={6}
                                        className="text-center py-8"
                                    >
                                        <div className="text-muted-foreground">
                                            <p className="text-lg font-medium">
                                                Loading bots...
                                            </p>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ) : error ? (
                                <TableRow>
                                    <TableCell
                                        colSpan={6}
                                        className="text-center py-8"
                                    >
                                        <div className="text-destructive">
                                            <p className="text-lg font-medium">
                                                Error loading bots
                                            </p>
                                            <p className="text-sm mt-1">
                                                {error}
                                            </p>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ) : bots.length === 0 ? (
                                <TableRow key={"no bots"}>
                                    <TableCell
                                        colSpan={6}
                                        className="text-center py-8"
                                    >
                                        <div className="text-muted-foreground">
                                            <p className="text-lg font-medium">
                                                No bots configured
                                            </p>
                                            <p className="text-sm mt-1">
                                                Add your first bot to get
                                                started
                                            </p>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                bots.map((bot) => (
                                    <TableRow key={bot.gitlabProjectId}>
                                        {/* Bot Name & Avatar */}
                                        <TableCell>
                                            {bot.hasBot ? (
                                                <div className="flex items-center gap-3">
                                                    <Avatar>
                                                        <AvatarImage
                                                            src={bot.avatar}
                                                            alt={bot.botName}
                                                        />
                                                        <AvatarFallback>
                                                            {bot.botName
                                                                ?.split(" ")
                                                                .map(
                                                                    (n) => n[0],
                                                                )
                                                                .join("")
                                                                .toUpperCase()}
                                                        </AvatarFallback>
                                                    </Avatar>
                                                    <div>
                                                        <p className="font-medium">
                                                            {bot.botName}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground">
                                                            ID: {bot.botId}
                                                        </p>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="flex items-center gap-3">
                                                    <Avatar>
                                                        <AvatarFallback>
                                                            <Settings className="h-4 w-4 text-muted-foreground" />
                                                        </AvatarFallback>
                                                    </Avatar>
                                                    <div>
                                                        <p className="text-sm text-muted-foreground italic">
                                                            No bot configured
                                                        </p>
                                                    </div>
                                                </div>
                                            )}
                                        </TableCell>

                                        {/* GitLab Project */}
                                        <TableCell>
                                            <a
                                                href={bot.projectUrl}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-primary hover:underline"
                                            >
                                                {bot.gitlabProject}
                                            </a>
                                        </TableCell>

                                        {/* Access Level */}
                                        <TableCell>
                                            {getAccessLevelBadge(
                                                bot.accessLevel,
                                            )}
                                        </TableCell>

                                        {/* Status */}
                                        <TableCell>
                                            {bot.hasBot ? (
                                                (() => {
                                                    const {
                                                        status,
                                                        errorMessage,
                                                        isLoading,
                                                    } = getBotStatus(bot);
                                                    if (isLoading) {
                                                        return (
                                                            <Badge
                                                                variant="outline"
                                                                className="text-muted-foreground"
                                                            >
                                                                <AlertCircle className="h-3 w-3 animate-pulse" />
                                                                Loading...
                                                            </Badge>
                                                        );
                                                    }
                                                    return status ? (
                                                        getStatusBadge(
                                                            status,
                                                            errorMessage,
                                                        )
                                                    ) : (
                                                        <Badge
                                                            variant="outline"
                                                            className="text-muted-foreground"
                                                        >
                                                            <AlertCircle className="h-3 w-3" />
                                                            Unknown
                                                        </Badge>
                                                    );
                                                })()
                                            ) : (
                                                <Badge
                                                    variant="outline"
                                                    className="text-muted-foreground"
                                                >
                                                    <AlertCircle className="h-3 w-3" />
                                                    Not Active
                                                </Badge>
                                            )}
                                        </TableCell>

                                        {/* Links */}
                                        <TableCell>
                                            {bot.hasBot ? (
                                                <div className="flex gap-1">
                                                    <TooltipProvider>
                                                        <Tooltip>
                                                            <TooltipTrigger
                                                                asChild
                                                            >
                                                                <Link
                                                                    href={`/dashboard/bots/${bot.botId}/stats`}
                                                                >
                                                                    <Button
                                                                        variant="outline"
                                                                        size="sm"
                                                                    >
                                                                        <BarChart3 className="h-4 w-4" />
                                                                    </Button>
                                                                </Link>
                                                            </TooltipTrigger>
                                                            <TooltipContent>
                                                                <p>
                                                                    View Stats
                                                                </p>
                                                            </TooltipContent>
                                                        </Tooltip>
                                                    </TooltipProvider>

                                                    <TooltipProvider>
                                                        <Tooltip>
                                                            <TooltipTrigger
                                                                asChild
                                                            >
                                                                <Link
                                                                    href={`/dashboard/bots/${bot.botId}/config`}
                                                                >
                                                                    <Button
                                                                        variant="outline"
                                                                        size="sm"
                                                                    >
                                                                        <Settings className="h-4 w-4" />
                                                                    </Button>
                                                                </Link>
                                                            </TooltipTrigger>
                                                            <TooltipContent>
                                                                <p>Configure</p>
                                                            </TooltipContent>
                                                        </Tooltip>
                                                    </TooltipProvider>
                                                </div>
                                            ) : (
                                                <Button
                                                    variant="default"
                                                    size="sm"
                                                    onClick={() =>
                                                        onCreateBot?.(
                                                            bot.gitlabProjectPathName,
                                                        )
                                                    }
                                                >
                                                    <Play className="mr-2 h-4 w-4" />
                                                    Create Bot
                                                </Button>
                                            )}
                                        </TableCell>

                                        {/* Actions */}
                                        <TableCell className="text-right">
                                            {bot.hasBot ? (
                                                (() => {
                                                    const { status } =
                                                        getBotStatus(bot);
                                                    return (
                                                        <DropdownMenu>
                                                            <DropdownMenuTrigger
                                                                asChild
                                                            >
                                                                <Button
                                                                    variant="outline"
                                                                    size="sm"
                                                                >
                                                                    <MoreVertical className="h-4 w-4" />
                                                                </Button>
                                                            </DropdownMenuTrigger>
                                                            <DropdownMenuContent align="end">
                                                                <DropdownMenuItem
                                                                    onClick={() =>
                                                                        handleStopBot(
                                                                            bot.botId!,
                                                                            bot.botName!,
                                                                        )
                                                                    }
                                                                    disabled={
                                                                        status ===
                                                                        "ERROR"
                                                                    }
                                                                >
                                                                    {status ===
                                                                    "STOPPED" ? (
                                                                        <>
                                                                            <Play className="mr-2 h-4 w-4" />
                                                                            Start
                                                                            Bot
                                                                        </>
                                                                    ) : (
                                                                        <>
                                                                            <StopCircle className="mr-2 h-4 w-4" />
                                                                            Stop
                                                                            Bot
                                                                        </>
                                                                    )}
                                                                </DropdownMenuItem>
                                                                <DropdownMenuItem
                                                                    onClick={() =>
                                                                        handleRevokeToken(
                                                                            bot.botId!,
                                                                            bot.botName!,
                                                                        )
                                                                    }
                                                                >
                                                                    <KeyRound className="mr-2 h-4 w-4" />
                                                                    Revoke Token
                                                                </DropdownMenuItem>
                                                                <DropdownMenuSeparator />
                                                                <DropdownMenuItem
                                                                    onClick={() =>
                                                                        handleRemoveBot(
                                                                            bot.botId!,
                                                                            bot.botName!,
                                                                        )
                                                                    }
                                                                    className="text-destructive focus:text-destructive"
                                                                >
                                                                    <Trash2 className="mr-2 h-4 w-4" />
                                                                    Remove Bot
                                                                </DropdownMenuItem>
                                                            </DropdownMenuContent>
                                                        </DropdownMenu>
                                                    );
                                                })()
                                            ) : (
                                                <span className="text-xs text-muted-foreground">
                                                    —
                                                </span>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </div>
            </div>

            {/* Custom Scrollbar Styles */}
            <style jsx global>{`
                .custom-scrollbar::-webkit-scrollbar {
                    height: 8px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: hsl(var(--muted));
                    border-radius: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: hsl(var(--muted-foreground) / 0.3);
                    border-radius: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: hsl(var(--muted-foreground) / 0.5);
                }
                /* Firefox */
                .custom-scrollbar {
                    scrollbar-width: thin;
                    scrollbar-color: hsl(var(--muted-foreground) / 0.3)
                        hsl(var(--muted));
                }
            `}</style>

            {/* Pagination Controls */}
            {totalBots > 0 && (
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <p className="text-sm text-muted-foreground">
                            Rows per page:
                        </p>
                        <Select
                            value={rowsPerPage.toString()}
                            onValueChange={(value) => {
                                setRowsPerPage(Number(value));
                                setCurrentPage(1);
                            }}
                        >
                            <SelectTrigger className="w-[70px]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="5">5</SelectItem>
                                <SelectItem value="10">10</SelectItem>
                                <SelectItem value="20">20</SelectItem>
                                <SelectItem value="50">50</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="flex items-center gap-2">
                        <p className="text-sm text-muted-foreground">
                            Page {currentPage} of {totalPages} ({totalBots}{" "}
                            total)
                        </p>
                        <div className="flex gap-1">
                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => setCurrentPage(1)}
                                            disabled={currentPage === 1}
                                        >
                                            <ChevronFirst className="h-4 w-4" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>First Page</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>

                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() =>
                                                setCurrentPage(currentPage - 1)
                                            }
                                            disabled={currentPage === 1}
                                        >
                                            <ChevronLeft className="h-4 w-4" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>Previous Page</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>

                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() =>
                                                setCurrentPage(currentPage + 1)
                                            }
                                            disabled={
                                                currentPage === totalPages
                                            }
                                        >
                                            <ChevronRight className="h-4 w-4" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>Next Page</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>

                            <TooltipProvider>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() =>
                                                setCurrentPage(totalPages)
                                            }
                                            disabled={
                                                currentPage === totalPages
                                            }
                                        >
                                            <ChevronLast className="h-4 w-4" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>Last Page</p>
                                    </TooltipContent>
                                </Tooltip>
                            </TooltipProvider>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
