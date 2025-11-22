"use client";

import { useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface CreateBotDialogProps {
    isOpen: boolean;
    onOpenChange: (open: boolean) => void;
    projectPathName: string | null;
    onCreateBot: (botName: string, projectPath: string) => Promise<void>;
}

export function CreateBotDialog({
    isOpen,
    onOpenChange,
    projectPathName,
    onCreateBot,
}: CreateBotDialogProps) {
    const [botName, setBotName] = useState("");
    const [isCreating, setIsCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);

    const handleCreate = async () => {
        if (!botName.trim()) {
            setCreateError("Bot name is required");
            return;
        }

        if (!projectPathName) {
            setCreateError("Project path is required");
            return;
        }

        setIsCreating(true);
        setCreateError(null);

        try {
            await onCreateBot(botName.trim(), projectPathName);

            // Success - close dialog and reset state
            setBotName("");
            setCreateError(null);
            onOpenChange(false);
        } catch (error) {
            console.error("Error creating bot:", error);
            setCreateError(
                error instanceof Error
                    ? error.message
                    : "An unexpected error occurred while creating the bot"
            );
        } finally {
            setIsCreating(false);
        }
    };

    const handleOpenChange = (open: boolean) => {
        if (!isCreating) {
            if (!open) {
                // Reset state when closing
                setBotName("");
                setCreateError(null);
            }
            onOpenChange(open);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleOpenChange}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Create Bot</DialogTitle>
                    <DialogDescription>
                        Configure a new bot for your GitLab project
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="project">GitLab Project</Label>
                        <Input
                            id="project"
                            value={projectPathName ?? ""}
                            readOnly
                            disabled
                            className="bg-muted"
                        />
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="bot-name">Bot Name *</Label>
                        <Input
                            id="bot-name"
                            value={botName}
                            onChange={(e) => setBotName(e.target.value)}
                            placeholder="e.g., code-review-bot"
                            disabled={isCreating}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !isCreating) {
                                    handleCreate();
                                }
                            }}
                        />
                    </div>

                    {createError && (
                        <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                            {createError}
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={() => handleOpenChange(false)}
                        disabled={isCreating}
                    >
                        Cancel
                    </Button>
                    <Button onClick={handleCreate} disabled={isCreating}>
                        {isCreating ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Creating...
                            </>
                        ) : (
                            "Create Bot"
                        )}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
