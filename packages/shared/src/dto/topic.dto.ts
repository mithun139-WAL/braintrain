export interface TopicRefDto {
    id: string;
    name: string;
}

export interface CreateTopicDto {
    name: string;
    description?: string;
    parentTopicId?: string;
}

export interface UpdateTopicDto {
    name?: string;
    description?: string;
    parentTopicId?: string;
}

export interface TopicDto {
    id: string;
    name: string;
    description?: string;
    isGlobal: boolean;
    createdByUserId?: string | null;
    parentTopicId?: string | null;
    createdAt: string | Date;
    updatedAt: string | Date;
    parentTopic?: TopicRefDto | null;
    subtopics?: TopicRefDto[];
    _count?: {
        sessions: number;
    };
    avgScore?: number;
    lastSessionDate?: string | Date | null;
    sessionCount?: number;
}
