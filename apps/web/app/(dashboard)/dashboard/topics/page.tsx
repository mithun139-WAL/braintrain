"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/core/components/ui/PageHeader";
import { Surface } from "@/core/components/ui/Surface";
import { buttonStyles } from "@/core/components/ui/button";
import { topicsApi } from "@/lib/api/topics.api";
import { TopicDto, CreateTopicDto } from "@braintrain/shared";
import { TopicCard } from "@/components/topics/TopicCard";
import { CreateTopicModal } from "@/components/topics/CreateTopicModal";
import { Search, Plus, BookOpen, Loader2, Layers, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { ConfirmationModal } from "@/components/ui/ConfirmationModal";

export default function TopicsPage() {
    const [topics, setTopics] = useState<TopicDto[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [filter, setFilter] = useState<"all" | "system" | "custom">("all");
    const [topicToDelete, setTopicToDelete] = useState<TopicDto | null>(null);

    const fetchTopics = async () => {
        try {
            setIsLoading(true);
            const response = await topicsApi.list();
            setTopics(response.data);
        } catch (error) {
            console.error("Failed to fetch topics:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchTopics();
    }, []);

    const handleCreateTopic = async (data: CreateTopicDto) => {
        try {
            setIsSubmitting(true);
            await topicsApi.create(data);
            setIsModalOpen(false);
            fetchTopics();
        } catch (error) {
            console.error("Failed to create topic:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDeleteTopic = async (id: string) => {
        try {
            await topicsApi.delete(id);
            setTopicToDelete(null);
            fetchTopics();
        } catch (error) {
            console.error("Failed to delete topic:", error);
        }
    };

    const filteredTopics = topics.filter(topic => {
        const matchesSearch = topic.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            topic.description?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesFilter = filter === "all" ||
            (filter === "system" && topic.isGlobal) ||
            (filter === "custom" && !topic.isGlobal);
        return matchesSearch && matchesFilter;
    });

    const customTopicCount = topics.filter((topic) => !topic.isGlobal).length;
    const systemTopicCount = topics.filter((topic) => topic.isGlobal).length;

    return (
        <div className="flex flex-col gap-8 pb-12">
            <PageHeader
                eyebrow="Knowledge Map"
                title="Topics"
                description="Shape the domains you want to practice, separate system topics from custom focus areas, and keep your practice library organized."
                meta={
                    <>
                        <TopicMeta label="All topics" value={topics.length} />
                        <TopicMeta label="System" value={systemTopicCount} />
                        <TopicMeta label="Custom" value={customTopicCount} />
                    </>
                }
                actions={
                    <button onClick={() => setIsModalOpen(true)} className={buttonStyles()}>
                        <Plus size={16} />
                        Create Topic
                    </button>
                }
            />

            <Surface padding="lg" className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(18rem,0.9fr)] lg:items-center">
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">
                        <Layers size={14} />
                        Library Controls
                    </div>
                    <div className="flex flex-col sm:flex-row gap-4">
                        <div className="relative flex-1 group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
                            <input
                                type="text"
                                placeholder="Search topics by name or description..."
                                className="h-12 w-full rounded-2xl border border-border bg-card pl-12 pr-4 text-sm font-medium text-foreground shadow-card outline-none transition-all focus:border-primary focus:ring-4 focus:ring-primary/5"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>
                        <div className="flex gap-2">
                            {(["all", "system", "custom"] as const).map((f) => (
                                <button
                                    key={f}
                                    onClick={() => setFilter(f)}
                                    className={cn(
                                        "h-12 rounded-2xl border px-5 text-sm font-bold capitalize transition-all",
                                        filter === f
                                            ? "border-primary/20 bg-primary/10 text-primary"
                                            : "border-border bg-card text-muted-foreground hover:border-primary/20 hover:text-foreground"
                                    )}
                                >
                                    {f}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <Surface variant="subtle" padding="lg" className="border-primary/10 bg-primary/5">
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.22em] text-primary/80">
                            <Sparkles size={14} />
                            Topic Strategy
                        </div>
                        <p className="text-body-sm text-muted-foreground">
                            Use system topics for broad interview coverage. Create custom topics when you want the AI to drill into a niche stack, role, or domain.
                        </p>
                    </div>
                </Surface>
            </Surface>

            {/* Grid Content */}
            {isLoading ? (
                <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
                    <Loader2 className="animate-spin text-primary" size={40} />
                    <p className="text-sm font-bold text-muted-foreground uppercase tracking-[0.18em]">Loading topics...</p>
                </div>
            ) : filteredTopics.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredTopics.map((topic) => (
                        <TopicCard
                            key={topic.id}
                            topic={topic}
                            onDelete={() => setTopicToDelete(topic)}
                        />
                    ))}
                </div>
            ) : (
                <Surface className="flex min-h-[400px] flex-col items-center justify-center border-2 border-dashed border-border bg-muted/20 p-12 text-center" padding="none">
                    <div className="size-20 rounded-2xl bg-primary/5 text-primary flex items-center justify-center mb-6">
                        <BookOpen size={40} />
                    </div>
                    <h3 className="mb-2 font-display text-title-lg text-foreground">
                        {searchQuery ? "No topics found" : "No topics available"}
                    </h3>
                    <p className="mb-8 max-w-sm text-body-sm font-medium leading-relaxed text-muted-foreground">
                        {searchQuery
                            ? "Try adjusting your search query or filters to find what you're looking for."
                            : "Start your practice journey by exploring global topics or creating your own custom focus areas."}
                    </p>
                    {!searchQuery && (
                        <button onClick={() => setIsModalOpen(true)} className={buttonStyles({ variant: "secondary" })}>
                            Create Your First Topic
                        </button>
                    )}
                </Surface>
            )}

            <CreateTopicModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onCreate={handleCreateTopic}
                isSubmitting={isSubmitting}
            />

            <ConfirmationModal
                isOpen={!!topicToDelete}
                onClose={() => setTopicToDelete(null)}
                onConfirm={() => topicToDelete && handleDeleteTopic(topicToDelete.id)}
                title="Delete custom topic?"
                description={topicToDelete ? `"${topicToDelete.name}" will be removed from your practice library.` : "This topic will be removed."}
                confirmText="Delete Topic"
                variant="danger"
            />
        </div>
    );
}

function TopicMeta({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm text-foreground shadow-card">
            <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{label}</span>
            <span className="font-semibold text-foreground">{value}</span>
        </div>
    );
}
