import { useEffect, useRef, useState } from "react";
import type { SkillPreference, SkillTag, User } from "@braintrain/shared";
import { BrainCircuit, Plus, X } from "lucide-react";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { cn } from "@/lib/utils";
import { useGetSkillTags } from "@/hooks/queries/useGetSkillTags";
import { useAddSkillPreference, useRemoveSkillPreference } from "@/hooks/mutations/useManageSkills";

interface SkillPreferencesCardProps {
    profile?: User;
    isLoading: boolean;
}

export function SkillPreferencesCard({ profile, isLoading }: SkillPreferencesCardProps) {
    const { data: tagsResponse, isLoading: isTagsLoading } = useGetSkillTags();
    const { mutate: addSkill, isPending: isAdding } = useAddSkillPreference();
    const { mutate: removeSkill, isPending: isRemoving } = useRemoveSkillPreference();
    const [showTagPicker, setShowTagPicker] = useState(false);
    const pickerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!showTagPicker) return;

        // Defer so the click that opened the picker isn't caught immediately
        let timer: ReturnType<typeof setTimeout>;
        function handleClickOutside(event: MouseEvent) {
            if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
                setShowTagPicker(false);
            }
        }

        timer = setTimeout(() => {
            document.addEventListener("mousedown", handleClickOutside);
        }, 0);

        return () => {
            clearTimeout(timer);
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [showTagPicker]);

    if (isLoading || isTagsLoading) {
        return <Surface padding="xl" className="min-h-[260px] animate-pulse" />;
    }

    const activeSkills = profile?.skillPreferences ?? [];
    const globalTags = tagsResponse?.data ?? [];
    const availableTags = globalTags.filter(
        (tag: SkillTag) => !activeSkills.some((preference: SkillPreference) => preference.skillTagId === tag.id)
    );

    const handleAddSkill = (skillTagId: string) => {
        addSkill(
            { skillTagId, level: "INTERMEDIATE" },
            {
                onSuccess: () => setShowTagPicker(false),
            }
        );
    };

    return (
        <Surface padding="xl" className="space-y-6">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div className="space-y-2">
                    <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">
                        <BrainCircuit size={14} />
                        Skill Focus
                    </div>
                    <h3 className="font-display text-title-lg text-foreground">Tune the skills that bias question generation</h3>
                    <p className="max-w-reading text-body-sm text-muted-foreground">
                        These focus tags weight the AI question generator and help shape the type of pressure your practice sessions create.
                    </p>
                </div>

                <div className="relative" ref={pickerRef}>
                    <button
                        type="button"
                        onClick={() => setShowTagPicker((value) => !value)}
                        className={buttonStyles({ variant: "secondary", size: "sm" })}
                    >
                        {showTagPicker ? <X size={14} /> : <Plus size={14} />}
                        {showTagPicker ? "Close" : "Add Skill"}
                    </button>

                    {showTagPicker ? (
                        <div className="absolute right-0 top-full z-50 mt-3 w-64 rounded-3xl border border-border bg-card p-2 shadow-elevated">
                            {availableTags.length === 0 ? (
                                <div className="px-3 py-4 text-center text-body-sm text-muted-foreground">
                                    All available skill tags are already active.
                                </div>
                            ) : (
                                <div className="max-h-72 overflow-y-auto">
                                    {availableTags.map((tag: SkillTag) => (
                                        <button
                                            key={tag.id}
                                            type="button"
                                            onClick={() => handleAddSkill(tag.id)}
                                            disabled={isAdding}
                                            className="flex w-full items-center justify-between rounded-2xl px-3 py-2 text-left text-sm font-medium text-foreground transition-colors hover:bg-muted"
                                        >
                                            <span>{tag.name}</span>
                                            <Plus size={14} className="text-primary" />
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    ) : null}
                </div>
            </div>

            {activeSkills.length === 0 ? (
                <Surface variant="subtle" padding="lg" className="border-dashed text-center">
                    <p className="text-sm font-semibold text-foreground">No focus skills selected yet</p>
                    <p className="mt-1 text-body-sm text-muted-foreground">
                        Add a few target skills to push the AI toward the areas you want to strengthen first.
                    </p>
                </Surface>
            ) : (
                <div className="flex flex-wrap gap-2">
                    {activeSkills.map((preference: SkillPreference) => (
                        <div
                            key={preference.id}
                            className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-2 text-sm font-semibold text-foreground shadow-card"
                        >
                            <span>{preference.skillTag?.name}</span>
                            <button
                                type="button"
                                onClick={() => removeSkill(preference.skillTagId)}
                                disabled={isRemoving}
                                className="text-muted-foreground transition-colors hover:text-ruby"
                                aria-label={`Remove ${preference.skillTag?.name}`}
                            >
                                <X size={14} />
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {availableTags.length > 0 ? (
                <div className="space-y-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                        Suggested tags
                    </p>
                    <div className="flex flex-wrap gap-2">
                        {availableTags.slice(0, 6).map((tag: SkillTag) => (
                            <button
                                key={tag.id}
                                type="button"
                                onClick={() => handleAddSkill(tag.id)}
                                disabled={isAdding}
                                className={cn(
                                    buttonStyles({ variant: "secondary", size: "sm" }),
                                    "h-auto rounded-full px-3 py-2"
                                )}
                            >
                                <Plus size={12} />
                                {tag.name}
                            </button>
                        ))}
                    </div>
                </div>
            ) : null}
        </Surface>
    );
}
