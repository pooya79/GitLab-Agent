import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

export default function StatsPage() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-3xl font-bold tracking-tight">
                    Statistics & Monitoring
                </h2>
                <p className="text-muted-foreground">
                    Monitor your GitLab Agent performance and usage metrics
                </p>
            </div>

            {/* Performance Metrics */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">
                            Total Requests
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">0</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            +0% from last month
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">
                            Success Rate
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">0%</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            No data available
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">
                            Avg Response Time
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">0ms</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            No data available
                        </p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-sm font-medium">
                            Active Connections
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">0</div>
                        <p className="text-xs text-muted-foreground mt-1">
                            Currently online
                        </p>
                    </CardContent>
                </Card>
            </div>

            {/* API Usage */}
            <Card>
                <CardHeader>
                    <CardTitle>API Usage</CardTitle>
                    <CardDescription>
                        Track your API endpoint usage over time
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <p className="text-sm font-medium">
                                    /api/v1/bot
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    Bot interactions
                                </p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm font-bold">0</p>
                                <p className="text-xs text-muted-foreground">
                                    requests
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <p className="text-sm font-medium">
                                    /api/v1/webhooks
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    Webhook events
                                </p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm font-bold">0</p>
                                <p className="text-xs text-muted-foreground">
                                    requests
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <p className="text-sm font-medium">
                                    /api/v1/gitlab
                                </p>
                                <p className="text-xs text-muted-foreground">
                                    GitLab API calls
                                </p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm font-bold">0</p>
                                <p className="text-xs text-muted-foreground">
                                    requests
                                </p>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* System Health */}
            <div className="grid gap-4 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>System Health</CardTitle>
                        <CardDescription>
                            Monitor service status and uptime
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-sm">API Server</span>
                                <span className="flex items-center gap-2 text-sm">
                                    <span className="h-2 w-2 rounded-full bg-green-500"></span>
                                    Online
                                </span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm">Database</span>
                                <span className="flex items-center gap-2 text-sm">
                                    <span className="h-2 w-2 rounded-full bg-green-500"></span>
                                    Connected
                                </span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm">
                                    GitLab Integration
                                </span>
                                <span className="flex items-center gap-2 text-sm">
                                    <span className="h-2 w-2 rounded-full bg-yellow-500"></span>
                                    Not Configured
                                </span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Resource Usage</CardTitle>
                        <CardDescription>
                            Monitor system resource consumption
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm">CPU Usage</span>
                                    <span className="text-sm font-medium">
                                        0%
                                    </span>
                                </div>
                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary"
                                        style={{ width: "0%" }}
                                    ></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm">
                                        Memory Usage
                                    </span>
                                    <span className="text-sm font-medium">
                                        0%
                                    </span>
                                </div>
                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary"
                                        style={{ width: "0%" }}
                                    ></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm">
                                        Storage Usage
                                    </span>
                                    <span className="text-sm font-medium">
                                        0%
                                    </span>
                                </div>
                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-primary"
                                        style={{ width: "0%" }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
