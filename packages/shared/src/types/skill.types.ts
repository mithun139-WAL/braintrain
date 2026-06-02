export interface SkillTag {
    id: string;
    name: string;
    isGlobal: boolean;
    createdAt: string;
}

export interface SkillPreference {
    id: string;
    userId: string;
    skillTagId: string;
    level: string;
    createdAt: string;
    updatedAt: string;
    skillTag: SkillTag;
}
