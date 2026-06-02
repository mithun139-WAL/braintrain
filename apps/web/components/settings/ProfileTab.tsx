import { useEffect, useState } from "react";
import type { User } from "@braintrain/shared";
import { Check, Mail, Pencil, Sparkles, X } from "lucide-react";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { cn } from "@/lib/utils";
import { useUpdateProfile } from "@/hooks/mutations/useUpdateProfile";

interface ProfileTabProps {
    profile?: User;
    isLoading: boolean;
}

function buildAvatarFallback(profile?: User) {
    return (profile?.displayName || profile?.email || "U").trim().charAt(0).toUpperCase();
}

function profileCompletion(profile?: User) {
    const checks = [Boolean(profile?.displayName), Boolean(profile?.bio), Boolean(profile?.avatarUrl)];
    return Math.round((checks.filter(Boolean).length / checks.length) * 100);
}

export function ProfileTab({ profile, isLoading }: ProfileTabProps) {
    const { mutate: updateProfile, isPending: isUpdating } = useUpdateProfile();
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState({
        displayName: profile?.displayName || "",
        bio: profile?.bio || "",
        avatarUrl: profile?.avatarUrl || "",
    });

    useEffect(() => {
        if (profile) {
            setEditForm({
                displayName: profile.displayName || "",
                bio: profile.bio || "",
                avatarUrl: profile.avatarUrl || "",
            });
        }
    }, [profile]);

    const handleSave = () => {
        updateProfile(editForm, {
            onSuccess: () => setIsEditing(false),
        });
    };

    if (isLoading) {
        return <Surface padding="xl" className="min-h-[320px] animate-pulse" />;
    }

    const completion = profileCompletion(profile);

    return (
        <Surface padding="xl" className="space-y-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
                <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
                    <div className="relative shrink-0">
                        <div className="flex size-24 items-center justify-center overflow-hidden rounded-3xl border border-border bg-muted text-3xl font-black text-muted-foreground shadow-card sm:size-28">
                            {editForm.avatarUrl || profile?.avatarUrl ? (
                                <img
                                    src={isEditing ? editForm.avatarUrl || profile?.avatarUrl || "" : profile?.avatarUrl || ""}
                                    alt={profile?.displayName || "User avatar"}
                                    className="h-full w-full object-cover"
                                />
                            ) : (
                                buildAvatarFallback(profile)
                            )}
                        </div>
                        <button
                            type="button"
                            onClick={() => setIsEditing((value) => !value)}
                            className="absolute -bottom-2 -right-2 flex size-10 items-center justify-center rounded-2xl border border-border bg-card text-muted-foreground shadow-card transition-colors hover:text-primary"
                            aria-label={isEditing ? "Stop editing profile" : "Edit profile"}
                        >
                            {isEditing ? <X size={16} /> : <Pencil size={16} />}
                        </button>
                    </div>

                    <div className="space-y-3">
                        <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-3">
                                <h2 className="font-display text-title-lg text-foreground">
                                    {profile?.displayName || "BrainTrain User"}
                                </h2>
                                <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-primary">
                                    <Sparkles size={12} />
                                    {(profile?.planType || "FREE").toUpperCase()} workspace
                                </span>
                            </div>
                            <div className="flex items-center gap-2 text-body-sm text-muted-foreground">
                                <Mail size={14} />
                                {profile?.email}
                            </div>
                        </div>

                        <p className="max-w-reading text-body-sm text-muted-foreground">
                            {profile?.bio ||
                                "Add a short bio and avatar so the coach and settings surfaces feel grounded around your actual practice identity."}
                        </p>
                    </div>
                </div>

                <div className="flex flex-wrap gap-3">
                    {isEditing ? (
                        <>
                            <button
                                type="button"
                                onClick={() => {
                                    setEditForm({
                                        displayName: profile?.displayName || "",
                                        bio: profile?.bio || "",
                                        avatarUrl: profile?.avatarUrl || "",
                                    });
                                    setIsEditing(false);
                                }}
                                className={buttonStyles({ variant: "secondary" })}
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={handleSave}
                                disabled={isUpdating}
                                className={buttonStyles()}
                            >
                                <Check size={16} />
                                {isUpdating ? "Saving..." : "Save Profile"}
                            </button>
                        </>
                    ) : (
                        <button type="button" onClick={() => setIsEditing(true)} className={buttonStyles({ variant: "secondary" })}>
                            <Pencil size={16} />
                            Edit Profile
                        </button>
                    )}
                </div>
            </div>

            {isEditing ? (
                <div className="grid gap-4 md:grid-cols-2">
                    <Field label="Display Name">
                        <input
                            type="text"
                            value={editForm.displayName}
                            onChange={(event) => setEditForm({ ...editForm, displayName: event.target.value })}
                            className="h-12 w-full rounded-2xl border border-border bg-card px-4 text-sm font-medium text-foreground outline-none transition-colors focus:border-primary"
                            placeholder="Your display name"
                        />
                    </Field>
                    <Field label="Avatar URL">
                        <input
                            type="url"
                            value={editForm.avatarUrl}
                            onChange={(event) => setEditForm({ ...editForm, avatarUrl: event.target.value })}
                            className="h-12 w-full rounded-2xl border border-border bg-card px-4 text-sm font-medium text-foreground outline-none transition-colors focus:border-primary"
                            placeholder="https://example.com/avatar.jpg"
                        />
                    </Field>
                    <Field label="Bio" className="md:col-span-2">
                        <textarea
                            value={editForm.bio}
                            onChange={(event) => setEditForm({ ...editForm, bio: event.target.value })}
                            className="min-h-[132px] w-full rounded-3xl border border-border bg-card px-4 py-3 text-sm text-foreground outline-none transition-colors focus:border-primary"
                            placeholder="What kind of interviews are you training for?"
                        />
                    </Field>
                </div>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-3">
                <ProfileMetric label="Profile completion" value={`${completion}%`} />
                <ProfileMetric label="Display identity" value={profile?.displayName ? "Configured" : "Needs name"} />
                <ProfileMetric label="Coach context" value={profile?.bio ? "Bio available" : "Needs bio"} />
            </div>
        </Surface>
    );
}

function Field({
    label,
    className,
    children,
}: {
    label: string;
    className?: string;
    children: React.ReactNode;
}) {
    return (
        <div className={cn("space-y-2", className)}>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
            {children}
        </div>
    );
}

function ProfileMetric({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-2xl border border-border bg-muted/30 px-4 py-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
            <p className="mt-2 text-sm font-semibold text-foreground">{value}</p>
        </div>
    );
}
