import { IsIn, IsString, IsNotEmpty } from 'class-validator';

export class AddSkillPreferenceDto {
    @IsString()
    @IsNotEmpty()
    skillTagId!: string;

    @IsIn(['BEGINNER', 'INTERMEDIATE', 'ADVANCED'])
    level!: 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
}
