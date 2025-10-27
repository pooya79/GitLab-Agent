"use client";

import { useState } from "react";
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

// Types
export interface Bot {
  id: string;
  gitlabProject: string;
  projectUrl: string;
  accessLevel: "Owner" | "Maintainer" | "Developer" | "Reporter" | "Guest";
  botName?: string; // Optional - null if no bot configured
  avatar?: string; // Optional - null if no bot configured
  status?: "active" | "stopped" | "error"; // Optional - null if no bot configured
  errorMessage?: string;
  hasBot: boolean; // Indicates if project has a bot configured
}

interface BotsTableProps {
  bots?: Bot[];
}

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

export function BotsTable({ bots = mockBots }: BotsTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Calculate pagination
  const totalPages = Math.ceil(bots.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const currentBots = bots.slice(startIndex, endIndex);

  const handleRemoveBot = (botId: string, botName: string) => {
    if (confirm(`Are you sure you want to remove "${botName}"?`)) {
      console.log("Removing bot:", botId);
      // Add your remove logic here
    }
  };

  const handleStopBot = (botId: string, botName: string) => {
    console.log("Stopping bot:", botId, botName);
    // Add your stop logic here
  };

  const handleRevokeToken = (botId: string, botName: string) => {
    if (
      confirm(`Are you sure you want to revoke the token for "${botName}"?`)
    ) {
      console.log("Revoking token for bot:", botId);
      // Add your revoke logic here
    }
  };

  const getStatusBadge = (status: Bot["status"], errorMessage?: string) => {
    switch (status) {
      case "active":
        return (
          <Badge variant="default" className="bg-green-600 hover:bg-green-700">
            <CheckCircle2 className="h-3 w-3" />
            Active
          </Badge>
        );
      case "stopped":
        return (
          <Badge variant="secondary">
            <Pause className="h-3 w-3" />
            Stopped
          </Badge>
        );
      case "error":
        return (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge variant="destructive" className="cursor-help">
                  <XCircle className="h-3 w-3" />
                  Error
                </Badge>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>{errorMessage || "An error occurred with this bot"}</p>
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
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentBots.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <div className="text-muted-foreground">
                      <p className="text-lg font-medium">No bots configured</p>
                      <p className="text-sm mt-1">
                        Add your first bot to get started
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                currentBots.map((bot) => (
                  <TableRow key={bot.id}>
                    {/* Bot Name & Avatar */}
                    <TableCell>
                      {bot.hasBot ? (
                        <div className="flex items-center gap-3">
                          <Avatar>
                            <AvatarImage src={bot.avatar} alt={bot.botName} />
                            <AvatarFallback>
                              {bot.botName
                                ?.split(" ")
                                .map((n) => n[0])
                                .join("")
                                .toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <p className="font-medium">{bot.botName}</p>
                            <p className="text-xs text-muted-foreground">
                              ID: {bot.id}
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
                      {getAccessLevelBadge(bot.accessLevel)}
                    </TableCell>

                    {/* Status */}
                    <TableCell>
                      {bot.hasBot && bot.status ? (
                        getStatusBadge(bot.status, bot.errorMessage)
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
                              <TooltipTrigger asChild>
                                <Link href={`/dashboard/bots/${bot.id}/stats`}>
                                  <Button variant="outline" size="sm">
                                    <BarChart3 className="h-4 w-4" />
                                  </Button>
                                </Link>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>View Stats</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>

                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Link href={`/dashboard/bots/${bot.id}/config`}>
                                  <Button variant="outline" size="sm">
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
                        <Link href={`/dashboard/bots/create?project=${bot.id}`}>
                          <Button variant="default" size="sm">
                            <Play className="mr-2 h-4 w-4" />
                            Create Bot
                          </Button>
                        </Link>
                      )}
                    </TableCell>

                    {/* Actions */}
                    <TableCell className="text-right">
                      {bot.hasBot ? (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() =>
                                handleStopBot(bot.id, bot.botName!)
                              }
                              disabled={bot.status === "error"}
                            >
                              {bot.status === "stopped" ? (
                                <>
                                  <Play className="mr-2 h-4 w-4" />
                                  Start Bot
                                </>
                              ) : (
                                <>
                                  <StopCircle className="mr-2 h-4 w-4" />
                                  Stop Bot
                                </>
                              )}
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() =>
                                handleRevokeToken(bot.id, bot.botName!)
                              }
                            >
                              <KeyRound className="mr-2 h-4 w-4" />
                              Revoke Token
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() =>
                                handleRemoveBot(bot.id, bot.botName!)
                              }
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Remove Bot
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
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
          scrollbar-color: hsl(var(--muted-foreground) / 0.3) hsl(var(--muted));
        }
      `}</style>

      {/* Pagination Controls */}
      {bots.length > 0 && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <p className="text-sm text-muted-foreground">Rows per page:</p>
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
              Page {currentPage} of {totalPages} ({bots.length} total)
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
                      onClick={() => setCurrentPage(currentPage - 1)}
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
                      onClick={() => setCurrentPage(currentPage + 1)}
                      disabled={currentPage === totalPages}
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
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
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
