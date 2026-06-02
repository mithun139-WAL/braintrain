export interface AddSkillPreferenceDto {
    skillTagId: string;
    level: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
}
