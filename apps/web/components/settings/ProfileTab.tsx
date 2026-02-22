import React, { useState, useEffect } from "react";
import { User } from "@braintrain/shared";
import { useAuthStore } from "@/lib/store/auth.store";
import { useUpdateProfile } from "@/hooks/mutations/useUpdateProfile";

interface ProfileTabProps {
    profile?: User;
    isLoading: boolean;
}

export function ProfileTab({ profile, isLoading }: ProfileTabProps) {
    const isPro = (profile?.planType || "FREE").toUpperCase() === "PRO";
    const { mutate: updateProfile, isPending: isUpdating } = useUpdateProfile();

    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState({
        displayName: profile?.displayName || "",
        bio: profile?.bio || "",
        avatarUrl: profile?.avatarUrl || ""
    });

    useEffect(() => {
        if (profile) {
            setEditForm({
                displayName: profile.displayName || "",
                bio: profile.bio || "",
                avatarUrl: profile.avatarUrl || ""
            });
        }
    }, [profile]);

    const handleSave = () => {
        updateProfile(editForm, {
            onSuccess: () => setIsEditing(false)
        });
    };

    if (isLoading) {
        return (
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 p-8 flex items-center justify-center animate-pulse min-h-[300px]">
                <div className="w-12 h-12 border-4 border-slate-200 border-t-primary rounded-full animate-spin"></div>
            </div>
        );
    }

    if (!isPro) {
        return (
            <div className="flex flex-col gap-6">
                {/* Profile Card */}
                <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-gray-100 dark:border-neutral-700 p-6 flex flex-col items-center text-center transition-colors">
                    <div className="relative">
                        <div className="h-24 w-24 rounded-full bg-slate-100 dark:bg-neutral-700 bg-cover bg-center border-4 border-white dark:border-neutral-800 shadow-sm overflow-hidden flex items-center justify-center">
                            {isEditing ? (
                                <img src={editForm.avatarUrl || "https://ui-avatars.com/api/?name=U"} alt="Preview" className="h-full w-full object-cover" />
                            ) : profile?.avatarUrl ? (
                                <img src={profile.avatarUrl} alt={profile.displayName || "User"} className="h-full w-full object-cover" />
                            ) : (
                                <span className="text-4xl font-black text-slate-300 dark:text-neutral-500 uppercase">
                                    {(profile?.displayName || profile?.email || "U")[0]}
                                </span>
                            )}
                        </div>
                        <div
                            className="absolute bottom-0 right-0 bg-gray-100 dark:bg-neutral-700 border border-white dark:border-neutral-600 rounded-full p-1.5 flex items-center justify-center cursor-pointer hover:bg-gray-200 dark:hover:bg-neutral-600 transition-colors"
                            onClick={() => setIsEditing(!isEditing)}
                        >
                            <span className="material-symbols-outlined text-gray-500 dark:text-neutral-300 text-sm">
                                {isEditing ? "close" : "edit"}
                            </span>
                        </div>
                    </div>
                    {isEditing ? (
                        <div className="mt-4 w-full space-y-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block text-left">Display Name</label>
                                <input
                                    type="text"
                                    value={editForm.displayName}
                                    onChange={(e) => setEditForm({ ...editForm, displayName: e.target.value })}
                                    className="w-full px-3 py-2 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg text-sm font-bold focus:outline-none focus:ring-1 focus:ring-primary"
                                    placeholder="Display Name"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block text-left">Bio</label>
                                <textarea
                                    value={editForm.bio}
                                    onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                                    className="w-full px-3 py-2 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg text-sm min-h-[80px] resize-none focus:outline-none focus:ring-1 focus:ring-primary"
                                    placeholder="Tell us about yourself..."
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block text-left">Avatar URL</label>
                                <input
                                    type="text"
                                    value={editForm.avatarUrl}
                                    onChange={(e) => setEditForm({ ...editForm, avatarUrl: e.target.value })}
                                    className="w-full px-3 py-2 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg text-[10px] focus:outline-none focus:ring-1 focus:ring-primary"
                                    placeholder="https://example.com/photo.jpg"
                                />
                            </div>
                            <button
                                onClick={handleSave}
                                disabled={isUpdating}
                                className="w-full py-2.5 bg-primary text-white rounded-lg text-sm font-bold shadow-sm hover:bg-primary-dark transition-colors disabled:opacity-50 mt-2"
                            >
                                {isUpdating ? "Saving..." : "Save Changes"}
                            </button>
                        </div>
                    ) : (
                        <div className="mt-4">
                            <h2 className="text-xl font-bold text-slate-900 dark:text-white leading-tight">
                                {profile?.displayName || "BrainTrain User"}
                            </h2>
                            <p className="text-sm text-slate-500 dark:text-neutral-400 mt-1">{profile?.email}</p>
                            {profile?.bio && (
                                <p className="text-xs text-slate-400 dark:text-neutral-500 mt-3 line-clamp-2 max-w-[240px]">
                                    {profile.bio}
                                </p>
                            )}
                        </div>
                    )}
                    <div className="mt-4">
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold bg-gray-100 dark:bg-neutral-700 text-gray-600 dark:text-neutral-300 border border-gray-200 dark:border-neutral-600 tracking-wider">
                            FREE PLAN
                        </span>
                    </div>
                </div>

                {/* Upgrade CTA */}
                <div className="relative overflow-hidden bg-primary/5 dark:bg-primary/10 rounded-xl border border-primary/10 dark:border-primary/20 p-6 transition-colors">
                    <div className="absolute -right-4 -top-4 w-24 h-24 bg-primary/10 rounded-full blur-2xl"></div>
                    <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-3 text-primary">
                            <span className="material-symbols-outlined text-xl">rocket_launch</span>
                            <span className="font-bold text-xs uppercase tracking-wider">Go Pro</span>
                        </div>
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2 leading-tight">Unlock Unlimited Potential</h3>
                        <p className="text-xs text-slate-600 dark:text-neutral-400 mb-6 leading-relaxed">
                            Upgrade to PRO to unlock 20 sessions/month, advanced analytics, and priority support.
                        </p>
                        <button className="w-full py-2.5 px-4 rounded-lg bg-primary hover:bg-primary-dark text-white text-sm font-bold shadow-sm transition-all flex items-center justify-center gap-2">
                            <span>Upgrade to PRO</span>
                            <span className="material-symbols-outlined text-lg">arrow_forward</span>
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-sm border border-neutral-200 dark:border-neutral-700 overflow-hidden mb-6 transition-colors">
            <div className="p-6 sm:p-8">
                <div className="flex flex-col md:flex-row gap-8 items-start">
                    {/* Avatar & Status */}
                    <div className="flex flex-col items-center gap-4 shrink-0 mx-auto md:mx-0">
                        <div className="relative group">
                            <div className="h-32 w-32 rounded-full bg-slate-100 dark:bg-neutral-700 ring-4 ring-white dark:ring-neutral-800 shadow-md flex items-center justify-center overflow-hidden">
                                {isEditing ? (
                                    <img src={editForm.avatarUrl || "https://ui-avatars.com/api/?name=U"} alt="Preview" className="h-full w-full object-cover" />
                                ) : profile?.avatarUrl ? (
                                    <img src={profile.avatarUrl} alt={profile.displayName || "User"} className="h-full w-full object-cover" />
                                ) : (
                                    <span className="text-5xl font-black text-slate-300 dark:text-neutral-500 uppercase">
                                        {(profile?.displayName || profile?.email || "U")[0]}
                                    </span>
                                )}
                            </div>
                            <button
                                className="absolute bottom-1 right-1 h-8 w-8 bg-white dark:bg-neutral-700 rounded-full shadow border border-neutral-200 dark:border-neutral-600 flex items-center justify-center text-neutral-600 dark:text-neutral-300 hover:text-primary transition-colors"
                                onClick={() => setIsEditing(true)}
                            >
                                <span className="material-symbols-outlined text-[18px]">edit</span>
                            </button>
                        </div>
                    </div>

                    {/* Details */}
                    <div className="flex-1 w-full text-center md:text-left">
                        <div className="flex flex-col md:flex-row items-center md:items-start justify-between gap-4">
                            <div className="w-full md:w-auto">
                                {isEditing ? (
                                    <div className="space-y-3">
                                        <div>
                                            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block mb-1">Display Name</label>
                                            <input
                                                type="text"
                                                value={editForm.displayName}
                                                onChange={(e) => setEditForm({ ...editForm, displayName: e.target.value })}
                                                className="w-full md:w-64 px-3 py-1.5 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg text-lg font-bold focus:outline-none focus:ring-1 focus:ring-primary"
                                                placeholder="Display Name"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block mb-1">Avatar URL</label>
                                            <input
                                                type="text"
                                                value={editForm.avatarUrl}
                                                onChange={(e) => setEditForm({ ...editForm, avatarUrl: e.target.value })}
                                                className="w-full md:w-full px-3 py-1 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg text-[11px] focus:outline-none focus:ring-1 focus:ring-primary font-mono"
                                                placeholder="https://example.com/photo.jpg"
                                            />
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-3 justify-center md:justify-start mb-1">
                                        <h2 className="text-2xl font-bold text-neutral-900 dark:text-white tracking-tight">
                                            {profile?.displayName || "BrainTrain User"}
                                        </h2>
                                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r from-primary to-primary-dark text-white shadow-sm shadow-primary/30 tracking-wider">
                                            <span className="material-symbols-outlined text-[14px] filled">verified</span>
                                            PRO
                                        </span>
                                    </div>
                                )}
                                <p className="text-neutral-500 dark:text-neutral-400 font-medium">{profile?.email}</p>
                            </div>
                            <div className="flex gap-3 mt-2 md:mt-0">
                                {isEditing ? (
                                    <>
                                        <button
                                            onClick={() => setIsEditing(false)}
                                            className="px-4 py-2 rounded-lg border border-neutral-200 dark:border-neutral-600 text-neutral-700 dark:text-neutral-200 text-sm font-bold hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleSave}
                                            disabled={isUpdating}
                                            className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-bold shadow-sm transition-colors flex items-center gap-2 disabled:opacity-50"
                                        >
                                            <span className="material-symbols-outlined text-[18px]">check</span>
                                            {isUpdating ? "Saving..." : "Save"}
                                        </button>
                                    </>
                                ) : (
                                    <button
                                        onClick={() => setIsEditing(true)}
                                        className="px-4 py-2 rounded-lg border border-neutral-200 dark:border-neutral-600 text-neutral-700 dark:text-neutral-200 text-sm font-bold hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
                                    >
                                        Edit Profile
                                    </button>
                                )}
                                <button className="px-4 py-2 rounded-lg bg-primary hover:bg-primary-dark text-white text-sm font-bold shadow-sm shadow-primary/20 transition-colors flex items-center gap-2">
                                    <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
                                    Manage Plan
                                </button>
                            </div>
                        </div>

                        {/* Editable Bio */}
                        <div className="mt-6 relative group/bio">
                            {isEditing ? (
                                <div>
                                    <label className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest block mb-2">About You</label>
                                    <textarea
                                        value={editForm.bio}
                                        onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                                        className="w-full px-4 py-3 bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-lg text-sm text-neutral-600 dark:text-neutral-300 focus:outline-none focus:ring-1 focus:ring-primary min-h-[100px] resize-none"
                                        placeholder="Tell us about yourself..."
                                    />
                                </div>
                            ) : (
                                <div className="w-full bg-transparent border-0 border-b border-transparent text-neutral-600 dark:text-neutral-300 p-0 text-sm leading-relaxed text-center md:text-left min-h-[3rem]">
                                    {profile?.bio || (
                                        <span className="text-neutral-400 italic italic">Add a short bio about yourself to help tailor your experience.</span>
                                    )}
                                </div>
                            )}
                            {!isEditing && (
                                <span
                                    className="material-symbols-outlined absolute top-0 -right-6 text-neutral-300 opacity-0 group-hover/bio:opacity-100 transition-opacity text-sm cursor-pointer md:block hidden"
                                    onClick={() => setIsEditing(true)}
                                >
                                    edit
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Stats Row */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 pt-8 border-t border-neutral-100 dark:border-neutral-700">
                    <div className="flex flex-col items-center md:items-start p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-100 dark:border-neutral-700">
                        <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-1">Sessions Completed</span>
                        <div className="flex items-baseline gap-1">
                            <span className="text-2xl font-bold text-neutral-900 dark:text-white">{profile?.monthlySessionCount || 0}</span>
                            <span className="text-xs text-neutral-500">total</span>
                        </div>
                    </div>
                    <div className="flex flex-col items-center md:items-start p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-100 dark:border-neutral-700">
                        <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-1">Credits Remaining</span>
                        <div className="flex items-baseline gap-1">
                            <span className="text-2xl font-bold text-neutral-900 dark:text-white">{profile?.monthlyEvaluationCredits || 0}</span>
                            <span className="text-xs text-neutral-500">/ 100</span>
                        </div>
                    </div>
                    <div className="flex flex-col items-center md:items-start p-4 rounded-lg bg-neutral-50 dark:bg-neutral-900/50 border border-neutral-100 dark:border-neutral-700">
                        <span className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-1">Billing Cycle</span>
                        <div className="flex items-baseline gap-1">
                            <span className="text-lg font-bold text-neutral-900 dark:text-white">
                                {profile?.createdAt ? new Date(profile.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : "-"}
                            </span>
                            <span className="text-xs text-neutral-500">next reset</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
