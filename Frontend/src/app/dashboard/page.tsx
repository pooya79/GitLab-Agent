import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { BotsTable } from "@/components/bots-table";

export default function DashboardPage() {
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
            <CardDescription>Connected GitLab projects</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">3</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Webhooks</CardTitle>
            <CardDescription>Active webhook listeners</CardDescription>
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
          <BotsTable />
        </CardContent>
      </Card>
    </div>
  );
}
