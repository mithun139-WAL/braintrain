import { useGetSkillTags } from "@/hooks/queries/useGetSkillTags";
import { useAddSkillPreference, useRemoveSkillPreference } from "@/hooks/mutations/useManageSkills";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface SkillPreferencesCardProps {
    profile?: any; // Using any because skillPreferences is not in the basic User interface yet
    isLoading: boolean;
}

export function SkillPreferencesCard({ profile, isLoading }: SkillPreferencesCardProps) {
    const isPro = (profile?.planType || "FREE").toUpperCase() === "PRO";
    const { data: tagsResponse, isLoading: isTagsLoading } = useGetSkillTags();
    const { mutate: addSkill, isPending: isAdding } = useAddSkillPreference();
    const { mutate: removeSkill, isPending: isRemoving } = useRemoveSkillPreference();

    const [showTagPicker, setShowTagPicker] = useState(false);
    const pickerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (pickerRef.current && !pickerRef.current.contains(event.target as Node)) {
                setShowTagPicker(false);
            }
        }
        if (showTagPicker) {
            document.addEventListener("mousedown", handleClickOutside);
        }
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [showTagPicker]);

    const handleAddSkill = (skillTagId: string) => {
        addSkill({ skillTagId, level: "INTERMEDIATE" }, {
            onSuccess: () => setShowTagPicker(false)
        });
    };

    const handleRemoveSkill = (skillTagId: string) => {
        removeSkill(skillTagId);
    };

    if (isLoading || isTagsLoading) {
        return (
            <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-neutral-200 dark:border-neutral-700 p-6 animate-pulse min-h-[200px]">
                <div className="h-6 w-1/2 bg-slate-200 dark:bg-neutral-700 rounded mb-4"></div>
                <div className="flex gap-2">
                    <div className="h-8 w-16 bg-slate-100 dark:bg-neutral-700 rounded-full"></div>
                    <div className="h-8 w-20 bg-slate-100 dark:bg-neutral-700 rounded-full"></div>
                </div>
            </div>
        );
    }

    // Map skillPreferences to simple string array if needed, or use as is
    const activeSkills = profile?.skillPreferences || [];
    const globalTags = tagsResponse?.data || [];
    const availableTags = globalTags.filter((tag: any) => !activeSkills.some((p: any) => p.skillTagId === tag.id));

    if (!isPro) {
        return (
            <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-gray-100 dark:border-neutral-700 p-6 transition-colors relative">
                <div className="mb-4">
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Skill Preferences</h3>
                </div>
                {activeSkills.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 border border-dashed border-gray-100 dark:border-neutral-700 rounded-lg">
                        <span className="material-symbols-outlined text-slate-300 dark:text-neutral-600 text-3xl mb-2">construction</span>
                        <p className="text-xs text-slate-400 dark:text-neutral-500 font-medium">No skills added yet</p>
                        <p className="text-[10px] text-slate-400 mt-1 italic">Add skills to tailor your mock interviews</p>
                    </div>
                ) : (
                    <div className="flex flex-wrap gap-2">
                        {activeSkills.map((pref: any) => (
                            <span key={pref.id} className="group relative px-3 py-1 bg-slate-50 dark:bg-neutral-900 border border-slate-100 dark:border-neutral-700 rounded-full text-xs font-medium text-slate-600 dark:text-neutral-400">
                                {pref.skillTag?.name}
                                <button
                                    onClick={() => handleRemoveSkill(pref.skillTagId)}
                                    className="ml-2 text-slate-300 hover:text-red-400 transition-colors"
                                    disabled={isRemoving}
                                >
                                    <span className="material-symbols-outlined text-[14px] align-middle">close</span>
                                </button>
                            </span>
                        ))}
                        <div className="relative" ref={pickerRef}>
                            <button
                                onClick={() => setShowTagPicker(!showTagPicker)}
                                className={cn(
                                    "h-7 w-7 flex items-center justify-center rounded-full border border-dashed transition-all",
                                    showTagPicker
                                        ? "bg-primary border-primary text-white scale-110 shadow-lg shadow-primary/20"
                                        : "bg-slate-50 dark:bg-neutral-700 border-slate-200 dark:border-neutral-600 text-slate-400 hover:text-primary hover:border-primary"
                                )}
                            >
                                <span className="material-symbols-outlined text-sm">{showTagPicker ? "close" : "add"}</span>
                            </button>

                            {showTagPicker && (
                                <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800 rounded-xl shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                                    <div className="p-3 border-b border-neutral-50 dark:border-neutral-800">
                                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Select Skill</p>
                                    </div>
                                    <div className="max-h-60 overflow-y-auto p-1">
                                        {availableTags.length === 0 ? (
                                            <div className="p-4 text-center">
                                                <p className="text-[10px] text-slate-400">All skills added!</p>
                                            </div>
                                        ) : (
                                            availableTags.map((tag: any) => (
                                                <button
                                                    key={tag.id}
                                                    onClick={() => handleAddSkill(tag.id)}
                                                    disabled={isAdding}
                                                    className="w-full flex items-center px-3 py-2 text-xs text-slate-600 dark:text-neutral-300 hover:bg-primary/5 hover:text-primary rounded-lg transition-colors text-left group"
                                                >
                                                    <span className="material-symbols-outlined text-sm mr-2 opacity-30 group-hover:opacity-100 transition-opacity">add_circle</span>
                                                    {tag.name}
                                                </button>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeSkills.length === 0 && globalTags.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-50 dark:border-neutral-700/50">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Suggested Skills</p>
                        <div className="flex flex-wrap gap-1.5">
                            {globalTags.filter((tag: any) => !activeSkills.some((p: any) => p.skillTagId === tag.id)).slice(0, 5).map((tag: any) => (
                                <button
                                    key={tag.id}
                                    onClick={() => handleAddSkill(tag.id)}
                                    disabled={isAdding}
                                    className="px-2 py-0.5 bg-neutral-50 dark:bg-neutral-800 rounded text-[10px] text-slate-500 hover:text-primary hover:bg-primary/5 transition-colors border border-transparent hover:border-primary/20"
                                >
                                    + {tag.name}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-neutral-200 dark:border-neutral-700 p-6 transition-colors">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-bold text-neutral-900 dark:text-white flex items-center gap-2 tracking-tight">
                    <span className="material-symbols-outlined text-primary">psychology</span>
                    Skill Focus
                </h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold bg-primary/10 text-primary tracking-widest uppercase">Targeted</span>
            </div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 mb-6 font-medium">Skills you are currently focusing on for your interviews.</p>

            <div className="flex flex-wrap gap-2 mb-8">
                {activeSkills.map((pref: any) => (
                    <div key={pref.id} className="group inline-flex items-center gap-2 px-3 py-1.5 bg-neutral-50 dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-700 rounded-full text-xs font-bold text-neutral-700 dark:text-neutral-300 transition-colors hover:bg-neutral-100 dark:hover:bg-neutral-800">
                        <span>{pref.skillTag?.name}</span>
                        <button
                            onClick={() => handleRemoveSkill(pref.skillTagId)}
                            className="text-neutral-300 group-hover:text-red-400 transition-colors"
                            disabled={isRemoving}
                        >
                            <span className="material-symbols-outlined text-[14px]">close</span>
                        </button>
                    </div>
                ))}

                {activeSkills.length < 10 && (
                    <div className="relative" ref={pickerRef}>
                        <button
                            onClick={() => setShowTagPicker(!showTagPicker)}
                            className={cn(
                                "h-8 w-8 flex items-center justify-center rounded-full border border-dashed transition-all outline-none",
                                showTagPicker
                                    ? "bg-primary border-primary text-white scale-110 shadow-lg shadow-primary/20"
                                    : "border-neutral-300 dark:border-neutral-600 text-neutral-400 hover:text-primary hover:border-primary"
                            )}
                        >
                            <span className="material-symbols-outlined text-[20px]">{showTagPicker ? "close" : "add"}</span>
                        </button>

                        {showTagPicker && (
                            <div className="absolute top-full left-0 mt-3 w-64 bg-white dark:bg-neutral-900 border border-neutral-100 dark:border-neutral-800 rounded-xl shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                                <div className="p-3 border-b border-neutral-50 dark:border-neutral-800">
                                    <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">Add Focus Skill</p>
                                </div>
                                <div className="max-h-64 overflow-y-auto p-1">
                                    {availableTags.length === 0 ? (
                                        <div className="p-4 text-center">
                                            <p className="text-[10px] text-slate-400">All skills added!</p>
                                        </div>
                                    ) : (
                                        availableTags.map((tag: any) => (
                                            <button
                                                key={tag.id}
                                                onClick={() => handleAddSkill(tag.id)}
                                                disabled={isAdding}
                                                className="w-full flex items-center px-4 py-2.5 text-xs text-slate-600 dark:text-neutral-300 hover:bg-primary/5 hover:text-primary rounded-lg transition-colors text-left group"
                                            >
                                                <span className="material-symbols-outlined text-sm mr-2 opacity-30 group-hover:opacity-100 transition-opacity">add_circle</span>
                                                {tag.name}
                                            </button>
                                        ))
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {activeSkills.length === 0 && globalTags.length > 0 && (
                <div className="mb-6 space-y-3">
                    <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest">Popular Focus Tags</p>
                    <div className="flex flex-wrap gap-2">
                        {globalTags.filter((tag: any) => !activeSkills.some((p: any) => p.skillTagId === tag.id)).slice(0, 8).map((tag: any) => (
                            <button
                                key={tag.id}
                                onClick={() => handleAddSkill(tag.id)}
                                disabled={isAdding}
                                className="px-3 py-1 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg text-xs text-neutral-500 hover:border-primary hover:text-primary transition-all shadow-sm"
                            >
                                {tag.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            <div className="bg-neutral-50 dark:bg-neutral-900/50 rounded-lg p-4 border border-neutral-100 dark:border-neutral-700">
                <div className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-primary text-[20px] shrink-0">info</span>
                    <p className="text-[11px] text-neutral-500 dark:text-neutral-400 leading-relaxed">
                        These skills are used to weight the AI question generator. You can have up to 10 active focus skills.
                    </p>
                </div>
            </div>
        </div>
    );
}
