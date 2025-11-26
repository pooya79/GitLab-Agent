"use client";

import { useState, useEffect, useRef, useCallback } from "react";
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
import { Input } from "@/components/ui/input";
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
    CheckCircle2,
    XCircle,
    Pause,
    StopCircle,
    Play,
    KeyRound,
    Trash2,
    AlertCircle,
    Loader2,
    Search,
} from "lucide-react";

type StatusLiterals = "ACTIVE" | "STOPPED" | "ERROR";

const PAGE_SIZE = 20;

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

export interface BotStatus {
    status: StatusLiterals;
    errorMessage?: string;
}

interface BotsTableProps {
    fetchBots: (
        page: number,
        perPage: number,
        search?: string,
    ) => Promise<Bot[]>;
    fetchBotStatus?: (botId: number) => Promise<BotStatus>;
    onCreateBot?: (projectPathName: string) => void;
    onStopBot?: (botId: number, botName: string) => Promise<void>;
    onCreateNewToken?: (botId: number, botName: string) => Promise<void>;
    onRemoveBot?: (botId: number, botName: string) => Promise<void>;
}

export function BotsTable({
    fetchBots,
    fetchBotStatus,
    onCreateBot,
    onStopBot,
    onCreateNewToken,
    onRemoveBot,
}: BotsTableProps) {
    const [page, setPage] = useState(1);
    const [bots, setBots] = useState<Bot[]>([]);
    const [hasMore, setHasMore] = useState(true);
    const [loadingState, setLoadingState] = useState<
        "idle" | "initial" | "more"
    >("initial");
    const [error, setError] = useState<string | null>(null);
    const [searchInput, setSearchInput] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [loadedPages, setLoadedPages] = useState(0);
    const [requestVersion, setRequestVersion] = useState(0);
    const [failedPage, setFailedPage] = useState<number | null>(null);
    const [botStatuses, setBotStatuses] = useState<Map<number, BotStatus>>(
        new Map(),
    );
    const [loadingStatuses, setLoadingStatuses] = useState<Set<number>>(
        new Set(),
    );
    const isLoading = loadingState !== "idle";
    const isInitialLoading = loadingState === "initial";
    const isFetchingMore = loadingState === "more";
    const observerRef = useRef<IntersectionObserver | null>(null);

    const handleLoadMore = useCallback(() => {
        if (!hasMore || isLoading) {
            return;
        }

        const nextPage = failedPage ?? loadedPages + 1;

        if (nextPage <= 0) {
            return;
        }

        if (page === nextPage) {
            if (failedPage !== null) {
                setRequestVersion((prev) => prev + 1);
            }
            return;
        }

        setPage(nextPage);
    }, [failedPage, hasMore, isLoading, loadedPages, page]);

    const loadMoreRef = useCallback(
        (node: HTMLDivElement | null) => {
            if (observerRef.current) {
                observerRef.current.disconnect();
            }

            if (!node) {
                return;
            }

            observerRef.current = new IntersectionObserver(
                (entries) => {
                    if (entries[0]?.isIntersecting) {
                        handleLoadMore();
                    }
                },
                {
                    root: null,
                    rootMargin: "200px",
                    threshold: 0,
                },
            );

            observerRef.current.observe(node);
        },
        [handleLoadMore],
    );

    useEffect(() => {
        return () => {
            observerRef.current?.disconnect();
        };
    }, []);

    useEffect(() => {
        const handler = setTimeout(() => {
            setSearchQuery(searchInput.trim());
        }, 400);

        return () => {
            clearTimeout(handler);
        };
    }, [searchInput]);

    useEffect(() => {
        setBots([]);
        setHasMore(true);
        setPage(1);
        setLoadedPages(0);
        setFailedPage(null);
    }, [searchQuery, fetchBots]);

    useEffect(() => {
        let isCancelled = false;

        const loadBots = async () => {
            setError(null);
            setFailedPage(null);
            setLoadingState(page === 1 ? "initial" : "more");

            try {
                const result = await fetchBots(page, PAGE_SIZE, searchQuery);
                if (isCancelled) {
                    return;
                }

                const nextBots = Array.isArray(result) ? result : [];

                setBots((prev) =>
                    page === 1 ? nextBots : [...prev, ...nextBots],
                );
                setHasMore(nextBots.length === PAGE_SIZE);
                setLoadedPages(page);
                setFailedPage(null);
            } catch (err) {
                if (!isCancelled) {
                    const message =
                        err instanceof Error
                            ? err.message
                            : "Failed to fetch bots";
                    setError(message);
                    setFailedPage(page);
                    console.error("Error fetching bots:", err);
                }
            } finally {
                if (!isCancelled) {
                    setLoadingState("idle");
                }
            }
        };

        loadBots();

        return () => {
            isCancelled = true;
        };
    }, [page, fetchBots, searchQuery, requestVersion]);

    // Fetch statuses for bots that have a bot configured
    useEffect(() => {
        if (!fetchBotStatus || bots.length === 0) return;

        const loadBotStatuses = async () => {
            // Mark all bot IDs as loading
            const botsWithBots = bots.filter((bot) => bot.hasBot);
            const loadingIds = new Set(botsWithBots.map((bot) => bot.botId!));
            setLoadingStatuses(loadingIds);

            // Clean up statuses for bots that no longer exist in the current list
            setBotStatuses((prev) => {
                const newMap = new Map(prev);
                const currentBotIds = new Set(
                    botsWithBots.map((bot) => bot.botId!),
                );
                // Remove statuses for bots that are no longer in the list
                for (const botId of newMap.keys()) {
                    if (!currentBotIds.has(botId)) {
                        newMap.delete(botId);
                    }
                }
                return newMap;
            });

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
                    const errorMessage =
                        err instanceof Error
                            ? err.message
                            : "Failed to fetch bot status";
                    console.error(
                        `Failed to fetch status for bot ID: ${bot.botId}:`,
                        err,
                    );

                    // Only set error status if it's not a "not found" error (deleted bot)
                    const isNotFoundError =
                        errorMessage.includes("not found") ||
                        errorMessage.includes("deleted");

                    if (!isNotFoundError) {
                        // Set error status if fetch fails for reasons other than bot deletion
                        setBotStatuses((prev) => {
                            const newMap = new Map(prev);
                            newMap.set(bot.botId!, {
                                status: "ERROR",
                                errorMessage: "Failed to fetch bot status",
                            });
                            return newMap;
                        });
                    }

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

    const handleRemoveBot = async (botId: number, botName: string) => {
        if (confirm(`Are you sure you want to remove "${botName}"?`)) {
            await onRemoveBot?.(botId, botName);
        }
    };

    const handleStopBot = async (botId: number, botName: string) => {
        await onStopBot?.(botId, botName);
    };

    const handleCreateNewToken = async (botId: number, botName: string) => {
        if (
            confirm(
                `Are you sure you want to create a new token for "${botName}"? This will invalidate the old token.`,
            )
        ) {
            await onCreateNewToken?.(botId, botName);
        }
    };

    const handleRetry = () => {
        setRequestVersion((prev) => prev + 1);
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

    const isSearching = searchQuery.length > 0;
    const emptyState = isSearching
        ? {
              title: "No matching projects",
              description: "Try a different search term.",
          }
        : {
              title: "No bots configured",
              description: "Add your first bot to get started",
          };
    const showErrorState = Boolean(error) && bots.length === 0;
    const showInlineError = Boolean(error) && bots.length > 0;

    return (
        <div className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="relative w-full sm:max-w-sm">
                    <Search
                        className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                        aria-hidden="true"
                    />
                    <Input
                        type="search"
                        value={searchInput}
                        onChange={(event) => setSearchInput(event.target.value)}
                        placeholder="Search projects"
                        className="pl-9"
                        aria-label="Search projects"
                    />
                </div>
                <p className="text-sm text-muted-foreground">
                    Showing {bots.length} project{bots.length === 1 ? "" : "s"}
                </p>
            </div>

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
                            {isInitialLoading ? (
                                <TableRow key="loading">
                                    <TableCell
                                        colSpan={6}
                                        className="py-8 text-center"
                                    >
                                        <div className="flex items-center justify-center gap-2 text-muted-foreground">
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            <span>Loading bots...</span>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ) : showErrorState ? (
                                <TableRow key="error">
                                    <TableCell
                                        colSpan={6}
                                        className="py-8 text-center"
                                    >
                                        <div className="text-destructive">
                                            <p className="text-lg font-medium">
                                                Error loading bots
                                            </p>
                                            <p className="mt-1 text-sm">
                                                {error}
                                            </p>
                                        </div>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="mt-4"
                                            onClick={handleRetry}
                                        >
                                            Try again
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ) : bots.length === 0 ? (
                                <TableRow key="no-bots">
                                    <TableCell
                                        colSpan={6}
                                        className="py-8 text-center"
                                    >
                                        <div className="text-muted-foreground">
                                            <p className="text-lg font-medium">
                                                {emptyState.title}
                                            </p>
                                            <p className="mt-1 text-sm">
                                                {emptyState.description}
                                            </p>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                <>
                                    {bots.map((bot) => (
                                        <TableRow key={bot.gitlabProjectId}>
                                            {/* Bot Name & Avatar */}
                                            <TableCell>
                                                {bot.hasBot ? (
                                                    <div className="flex items-center gap-3">
                                                        <Avatar>
                                                            <AvatarImage
                                                                src={bot.avatar}
                                                                alt={
                                                                    bot.botName
                                                                }
                                                            />
                                                            <AvatarFallback>
                                                                {bot.botName
                                                                    ?.split(" ")
                                                                    .map(
                                                                        (n) =>
                                                                            n[0],
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
                                                                No bot
                                                                configured
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
                                                                        View
                                                                        Stats
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
                                                                        href={`/dashboard/bots/${bot.botId}/configs`}
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
                                                                    <p>
                                                                        Configure
                                                                    </p>
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
                                                                            handleCreateNewToken(
                                                                                bot.botId!,
                                                                                bot.botName!,
                                                                            )
                                                                        }
                                                                    >
                                                                        <KeyRound className="mr-2 h-4 w-4" />
                                                                        Create
                                                                        New
                                                                        Token
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
                                                                        Remove
                                                                        Bot
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
                                    ))}
                                    {isFetchingMore && (
                                        <TableRow key="loading-more">
                                            <TableCell
                                                colSpan={6}
                                                className="py-6 text-center"
                                            >
                                                <div className="flex items-center justify-center gap-2 text-muted-foreground">
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                    <span>
                                                        Loading more bots...
                                                    </span>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </>
                            )}
                        </TableBody>
                    </Table>
                </div>
            </div>

            {showInlineError && (
                <div className="flex flex-col items-center justify-center gap-2 text-sm text-destructive sm:flex-row">
                    <span>Failed to load more bots: {error}</span>
                    <Button variant="outline" size="sm" onClick={handleRetry}>
                        Try again
                    </Button>
                </div>
            )}

            <div ref={loadMoreRef} aria-hidden="true" className="h-px w-full" />

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
        </div>
    );
}
