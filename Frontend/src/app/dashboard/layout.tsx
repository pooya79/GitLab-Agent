"use client";

import { ProtectedRoute, useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
    NavigationMenu,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
    navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getGitlabUserinfoApiV1GitlabUserinfoGet } from "@/client";
import type { AppSchemasGitlabUserInfo } from "@/client";
import { useEffect, useState } from "react";
import { User, Mail, ExternalLink, LogOut } from "lucide-react";

function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { logout } = useAuth();
    const [userInfo, setUserInfo] = useState<AppSchemasGitlabUserInfo | null>(
        null,
    );

    useEffect(() => {
        const fetchUserInfo = async () => {
            try {
                const result = await getGitlabUserinfoApiV1GitlabUserinfoGet();
                if (result.response.status === 401) {
                    // Unauthorized, logout the user
                    logout();
                } else if (result.data) {
                    console.log("User info fetched successfully:", result.data);
                    setUserInfo(result.data);
                }
            } catch (error) {
                console.error("Failed to fetch user info:", error);
                logout();
            }
        };

        fetchUserInfo();
    }, []);

    return (
        <ProtectedRoute>
            <div className="min-h-screen">
                {/* Dashboard Header */}
                <header className="border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
                    <div className="container mx-auto flex h-16 items-center justify-between px-8">
                        <div className="flex items-center gap-6">
                            <h1 className="text-xl font-bold">GitLab Agent</h1>
                            <NavigationMenu>
                                <NavigationMenuList>
                                    <NavigationMenuItem>
                                        <NavigationMenuLink asChild>
                                            <Link href="/dashboard">
                                                Dashboard
                                            </Link>
                                        </NavigationMenuLink>
                                    </NavigationMenuItem>
                                    <NavigationMenuItem>
                                        <NavigationMenuLink asChild>
                                            <Link href="/dashboard/stats">
                                                Stats
                                            </Link>
                                        </NavigationMenuLink>
                                    </NavigationMenuItem>
                                </NavigationMenuList>
                            </NavigationMenu>
                        </div>

                        {/* User Info Dropdown */}
                        {userInfo ? (
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button
                                        variant="ghost"
                                        className="relative h-10 w-10 rounded-full"
                                    >
                                        <Avatar className="h-10 w-10">
                                            <AvatarImage
                                                src={
                                                    userInfo.avatar_url ||
                                                    undefined
                                                }
                                                alt={
                                                    userInfo.name ||
                                                    userInfo.username
                                                }
                                            />
                                            <AvatarFallback>
                                                {userInfo.name
                                                    ?.charAt(0)
                                                    .toUpperCase() ||
                                                    userInfo.username
                                                        .charAt(0)
                                                        .toUpperCase()}
                                            </AvatarFallback>
                                        </Avatar>
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent
                                    className="w-64"
                                    align="end"
                                    forceMount
                                >
                                    <DropdownMenuLabel className="font-normal">
                                        <div className="flex flex-col space-y-2">
                                            <div className="flex items-center gap-2">
                                                <Avatar className="h-12 w-12">
                                                    <AvatarImage
                                                        src={
                                                            userInfo.avatar_url ||
                                                            undefined
                                                        }
                                                        alt={
                                                            userInfo.name ||
                                                            userInfo.username
                                                        }
                                                    />
                                                    <AvatarFallback>
                                                        {userInfo.name
                                                            ?.charAt(0)
                                                            .toUpperCase() ||
                                                            userInfo.username
                                                                .charAt(0)
                                                                .toUpperCase()}
                                                    </AvatarFallback>
                                                </Avatar>
                                                <div className="flex flex-col flex-1 min-w-0">
                                                    <p className="text-sm font-medium leading-none truncate">
                                                        {userInfo.name ||
                                                            userInfo.username}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground mt-1 truncate">
                                                        @{userInfo.username}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                                <Mail className="h-3 w-3" />
                                                <span className="truncate">
                                                    {userInfo.email}
                                                </span>
                                            </div>
                                        </div>
                                    </DropdownMenuLabel>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem asChild>
                                        <a
                                            href={userInfo.web_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="cursor-pointer flex items-center"
                                        >
                                            <ExternalLink className="mr-2 h-4 w-4" />
                                            <span>View GitLab Profile</span>
                                        </a>
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                        onClick={logout}
                                        className="cursor-pointer text-red-600"
                                    >
                                        <LogOut className="mr-2 h-4 w-4" />
                                        <span>Logout</span>
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        ) : (
                            <Button
                                onClick={logout}
                                variant="outline"
                                size="sm"
                            >
                                Logout
                            </Button>
                        )}
                    </div>
                </header>

                {/* Dashboard Content */}
                <main className="container mx-auto p-8">{children}</main>
            </div>
        </ProtectedRoute>
    );
}

export default DashboardLayout;
