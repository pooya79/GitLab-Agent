"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
    getAvailableAvatarsApiV1ConfigAvailableAvatarsGet,
    getAvailableLlmsApiV1ConfigAvailableLlmsGet,
    getBotApiV1BotsBotIdGet,
    updateBotApiV1BotsBotIdPatch,
} from "@/client/sdk.gen";
import { type BotRead, type LlmModelInfo } from "@/client/types.gen";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

type AvatarOption = {
    name: string;
    url: string;
};

type LlmOption = LlmModelInfo & {
    id: string;
};

const normalizeAvailableAvatars = (raw: unknown): AvatarOption[] => {
    if (!raw || typeof raw !== "object") return [];
    return Object.entries(raw as Record<string, unknown>).map(
        ([name, url]) => ({
            name,
            url: typeof url === "string" ? url : "",
        }),
    );
};

const fetchBotById = async (botId: number): Promise<BotRead> => {
    const response = await getBotApiV1BotsBotIdGet({
        path: { bot_id: botId },
    });

    if (response.error) {
        throw new Error("Failed to load bot.");
    }

    if (response.response.status !== 200) {
        throw new Error(`Unable to load bot: ${response.response.statusText}`);
    }

    return response.data;
};

export default function BotConfigsPage() {
    const params = useParams<{ botId?: string }>();
    const botId = Number(params?.botId);
    const isValidBotId = Number.isFinite(botId);

    const [bot, setBot] = useState<BotRead | null>(null);
    const [availableAvatars, setAvailableAvatars] = useState<AvatarOption[]>(
        [],
    );
    const [availableLlms, setAvailableLlms] = useState<LlmOption[]>([]);
    const [avatarName, setAvatarName] = useState("");
    const [llmModel, setLlmModel] = useState("");
    const [systemPrompt, setSystemPrompt] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [saveError, setSaveError] = useState<string | null>(null);
    const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

    const selectedAvatar = useMemo(
        () => availableAvatars.find((item) => item.name === avatarName),
        [avatarName, availableAvatars],
    );

    const selectedLlm = useMemo(
        () => availableLlms.find((item) => item.id === llmModel),
        [availableLlms, llmModel],
    );

    const loadPage = useCallback(async () => {
        if (!isValidBotId) {
            setError("Invalid bot ID in the URL.");
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);
        setSaveError(null);
        setSaveSuccess(null);

        try {
            const [avatarResponse, llmResponse, botData] = await Promise.all([
                getAvailableAvatarsApiV1ConfigAvailableAvatarsGet(),
                getAvailableLlmsApiV1ConfigAvailableLlmsGet(),
                fetchBotById(botId),
            ]);

            if (avatarResponse.error) {
                throw new Error("Unable to fetch available avatars.");
            }
            if (avatarResponse.response.status !== 200) {
                throw new Error(
                    `Unable to fetch available avatars: ${avatarResponse.response.statusText}`,
                );
            }

            if (llmResponse.error) {
                throw new Error("Unable to fetch available LLMs.");
            }
            if (llmResponse.response.status !== 200) {
                throw new Error(
                    `Unable to fetch available LLMs: ${llmResponse.response.statusText}`,
                );
            }

            const normalizedAvatars = normalizeAvailableAvatars(
                avatarResponse.data ?? [],
            );
            const avatarOptions = normalizedAvatars.some(
                (item) => item.name === botData.avatar_name,
            )
                ? normalizedAvatars
                : botData.avatar_name
                  ? [
                        {
                            name: botData.avatar_name,
                            url: botData.avatar_url ?? "",
                        },
                        ...normalizedAvatars,
                    ]
                  : normalizedAvatars;
            setAvailableAvatars(avatarOptions);

            const llmMap = llmResponse.data ?? {};
            let llmOptions = Object.entries(llmMap).map(([id, info]) => ({
                id,
                model_name: info?.model_name ?? id,
                context_window: info?.context_window ?? 0,
                max_output_tokens: info?.max_output_tokens ?? 0,
                temperature: info?.temperature ?? 0,
                additional_kwargs_schema: info?.additional_kwargs_schema,
            }));
            if (
                botData.llm_model &&
                !llmOptions.some((llm) => llm.id === botData.llm_model)
            ) {
                llmOptions = [
                    {
                        id: botData.llm_model,
                        model_name: botData.llm_model,
                        context_window: 0,
                        max_output_tokens: botData.llm_max_output_tokens,
                        temperature: botData.llm_temperature,
                        additional_kwargs_schema:
                            botData.llm_additional_kwargs ?? {},
                    },
                    ...llmOptions,
                ];
            }
            setAvailableLlms(llmOptions);

            setBot(botData);
            const nextAvatar =
                botData.avatar_name ?? avatarOptions[0]?.name ?? "";
            setAvatarName(nextAvatar);
            const nextLlmModel = botData.llm_model || llmOptions[0]?.id || "";
            setLlmModel(nextLlmModel);
            setSystemPrompt(botData.llm_system_prompt ?? "");
        } catch (e) {
            setError(
                e instanceof Error
                    ? e.message
                    : "Something went wrong loading this bot.",
            );
        } finally {
            setLoading(false);
        }
    }, [botId, isValidBotId]);

    useEffect(() => {
        loadPage();
    }, [loadPage]);

    const handleSave = async () => {
        if (!isValidBotId) {
            setSaveError("Invalid bot ID. Reload the page and try again.");
            return;
        }

        setSaving(true);
        setSaveError(null);
        setSaveSuccess(null);

        try {
            const response = await updateBotApiV1BotsBotIdPatch({
                path: { bot_id: botId },
                body: {
                    avatar_name: avatarName || null,
                    llm_model: llmModel || null,
                    llm_system_prompt: systemPrompt || null,
                },
            });

            if (response.error) {
                throw new Error("Failed to update bot.");
            }
            if (response.response.status !== 200) {
                throw new Error(
                    `Failed to update bot: ${response.response.statusText}`,
                );
            }

            const updated = response.data.bot;
            setBot(updated);
            setAvatarName(updated.avatar_name ?? avatarName);
            setLlmModel(updated.llm_model ?? llmModel);
            setSystemPrompt(updated.llm_system_prompt ?? systemPrompt);
            setSaveSuccess("Bot configuration updated.");
        } catch (e) {
            setSaveError(
                e instanceof Error
                    ? e.message
                    : "Something went wrong while saving.",
            );
        } finally {
            setSaving(false);
        }
    };

    const renderAvatarPreview = () => {
        const preview = selectedAvatar ?? {
            name: avatarName || bot?.avatar_name || "No avatar",
            url: bot?.avatar_url ?? "",
        };

        return (
            <div className="flex items-center gap-3 rounded-md border p-3">
                <Avatar className="h-12 w-12">
                    <AvatarImage src={preview.url} alt={preview.name} />
                    <AvatarFallback>
                        {preview.name.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                </Avatar>
                <div className="space-y-1">
                    <div className="font-semibold">{preview.name}</div>
                    <p className="text-xs text-muted-foreground">
                        {preview.url || "No avatar URL returned"}
                    </p>
                </div>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between gap-3">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight">
                            Bot configuration
                        </h2>
                        <p className="text-muted-foreground">
                            Manage avatar and LLM settings for this bot.
                        </p>
                    </div>
                    <Button variant="outline" asChild>
                        <Link href="/dashboard">Back to dashboard</Link>
                    </Button>
                </div>
                <p className="text-sm text-muted-foreground">
                    Bot ID: {isValidBotId ? botId : "Unknown"}
                </p>
            </div>

            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Couldn&apos;t load bot</AlertTitle>
                    <AlertDescription className="flex flex-col gap-2">
                        <span>{error}</span>
                        <div className="flex gap-2">
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={loadPage}
                            >
                                Retry
                            </Button>
                            <Button size="sm" variant="ghost" asChild>
                                <Link href="/dashboard">Go back</Link>
                            </Button>
                        </div>
                    </AlertDescription>
                </Alert>
            )}

            <div className="grid gap-4 lg:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Avatar</CardTitle>
                        <CardDescription>
                            Choose an avatar for this bot. Available options
                            come from the API.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {loading ? (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading avatars...
                            </div>
                        ) : (
                            <>
                                <div className="space-y-2">
                                    <Label htmlFor="avatar-select">
                                        Avatar
                                    </Label>
                                    <Select
                                        value={avatarName}
                                        onValueChange={setAvatarName}
                                        disabled={!availableAvatars.length}
                                    >
                                        <SelectTrigger id="avatar-select">
                                            <SelectValue placeholder="Select an avatar" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {availableAvatars.map((avatar) => (
                                                <SelectItem
                                                    key={avatar.name}
                                                    value={avatar.name}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <Avatar className="h-6 w-6">
                                                            <AvatarImage
                                                                src={avatar.url}
                                                                alt={
                                                                    avatar.name
                                                                }
                                                            />
                                                            <AvatarFallback>
                                                                {avatar.name
                                                                    .slice(0, 2)
                                                                    .toUpperCase()}
                                                            </AvatarFallback>
                                                        </Avatar>
                                                        <span className="truncate">
                                                            {avatar.name}
                                                        </span>
                                                    </div>
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <p className="text-xs text-muted-foreground">
                                        If left empty, the bot keeps its current
                                        avatar.
                                    </p>
                                </div>
                                {renderAvatarPreview()}
                            </>
                        )}
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>LLM</CardTitle>
                        <CardDescription>
                            Pick which model this bot should use and set a
                            system prompt.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {loading ? (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Loading LLMs...
                            </div>
                        ) : (
                            <>
                                <div className="space-y-2">
                                    <Label htmlFor="llm-select">
                                        LLM model
                                    </Label>
                                    <Select
                                        value={llmModel}
                                        onValueChange={setLlmModel}
                                        disabled={!availableLlms.length}
                                    >
                                        <SelectTrigger id="llm-select">
                                            <SelectValue placeholder="Select a model" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            {availableLlms.map((llm) => (
                                                <SelectItem
                                                    key={llm.id}
                                                    value={llm.id}
                                                >
                                                    {llm.id} · {llm.model_name}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <div className="text-xs text-muted-foreground">
                                        {selectedLlm ? (
                                            <div className="space-y-1">
                                                <p>
                                                    Context:{" "}
                                                    {selectedLlm.context_window.toLocaleString()}{" "}
                                                    tokens
                                                </p>
                                                <p>
                                                    Max output:{" "}
                                                    {selectedLlm.max_output_tokens.toLocaleString()}{" "}
                                                    tokens
                                                </p>
                                                <p>
                                                    Temperature:{" "}
                                                    {selectedLlm.temperature.toFixed(
                                                        2,
                                                    )}
                                                </p>
                                            </div>
                                        ) : (
                                            "Select a model to view details."
                                        )}
                                    </div>
                                </div>

                                <Separator />

                                <div className="space-y-2">
                                    <Label htmlFor="system-prompt">
                                        System prompt
                                    </Label>
                                    <textarea
                                        id="system-prompt"
                                        value={systemPrompt}
                                        onChange={(e) =>
                                            setSystemPrompt(e.target.value)
                                        }
                                        className="flex min-h-[140px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                        placeholder="Provide instructions that guide how the bot should respond."
                                    />
                                    <p className="text-xs text-muted-foreground">
                                        Leave blank to keep the existing system
                                        prompt.
                                    </p>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>

            {saveError && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Could not save</AlertTitle>
                    <AlertDescription>{saveError}</AlertDescription>
                </Alert>
            )}

            {saveSuccess && (
                <Alert>
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertTitle>Saved</AlertTitle>
                    <AlertDescription>{saveSuccess}</AlertDescription>
                </Alert>
            )}

            <div className="flex flex-wrap gap-3">
                <Button onClick={handleSave} disabled={saving || loading}>
                    {saving ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Saving...
                        </>
                    ) : (
                        "Save configuration"
                    )}
                </Button>
                <Button variant="outline" onClick={loadPage} disabled={loading}>
                    Reload
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Bot details</CardTitle>
                    <CardDescription>
                        Current values returned by the bots API.
                    </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                            Bot name
                        </p>
                        <p className="font-medium">
                            {bot?.gitlab_user_name ?? "—"}
                        </p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                            GitLab project
                        </p>
                        <p className="font-medium">
                            {bot?.gitlab_project_path ?? "—"}
                        </p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                            LLM model
                        </p>
                        <p className="font-medium">{bot?.llm_model ?? "—"}</p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Avatar</p>
                        <p className="font-medium">{bot?.avatar_name ?? "—"}</p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                            Max output tokens
                        </p>
                        <p className="font-medium">
                            {bot
                                ? bot.llm_max_output_tokens.toLocaleString()
                                : "—"}
                        </p>
                    </div>
                    <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">
                            Temperature
                        </p>
                        <p className="font-medium">
                            {typeof bot?.llm_temperature === "number"
                                ? bot.llm_temperature.toFixed(2)
                                : "—"}
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
