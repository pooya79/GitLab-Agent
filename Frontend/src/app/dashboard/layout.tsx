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
import Link from "next/link";
import { usePathname } from "next/navigation";

function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { logout } = useAuth();

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
                        <Button onClick={logout} variant="outline" size="sm">
                            Logout
                        </Button>
                    </div>
                </header>

                {/* Dashboard Content */}
                <main className="container mx-auto p-8">{children}</main>
            </div>
        </ProtectedRoute>
    );
}

export default DashboardLayout;
