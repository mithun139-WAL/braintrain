import { IsNotEmpty, IsString, IsEnum, IsBoolean, IsInt, Min, IsOptional, IsObject } from 'class-validator';
import { DifficultyLevel, InterviewMode } from '@prisma/client';

export class CreateSessionDto {
    @IsNotEmpty()
    @IsString()
    topicId!: string;

    @IsNotEmpty()
    @IsEnum(InterviewMode)
    mode!: InterviewMode;

    @IsNotEmpty()
    @IsEnum(DifficultyLevel)
    difficulty!: DifficultyLevel;

    @IsNotEmpty()
    @IsBoolean()
    adaptive!: boolean;

    @IsNotEmpty()
    @IsInt()
    @Min(5)
    durationMinutes!: number;

    @IsOptional()
    @IsObject()
    personalityConfig?: Record<string, any>;
}
