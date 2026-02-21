import { IsNotEmpty, IsString, IsEnum, IsOptional, IsIn, MaxLength } from 'class-validator';
import { DifficultyLevel } from '@prisma/client';

export class CreateQuestionBankDto {
    @IsString()
    @IsNotEmpty()
    @MaxLength(1000)
    content!: string;

    @IsString()
    @IsNotEmpty()
    topicId!: string;

    @IsEnum(DifficultyLevel)
    difficulty!: DifficultyLevel;

    @IsIn(['behavioral', 'technical'])
    questionType!: 'behavioral' | 'technical';

    @IsOptional()
    isGlobal?: boolean;
}
