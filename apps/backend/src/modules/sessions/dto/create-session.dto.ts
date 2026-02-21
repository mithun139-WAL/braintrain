import { IsNotEmpty, IsString, IsEnum, IsBoolean, IsInt, Min, IsOptional, IsObject } from 'class-validator';
import { DifficultyLevel, InterviewLevel, InterviewMode } from '@prisma/client';

export class CreateSessionDto {
    @IsNotEmpty()
    @IsString()
    topicId!: string;

    @IsNotEmpty()
    @IsEnum(InterviewMode)
    mode!: InterviewMode;

    @IsOptional()
    @IsEnum(InterviewLevel)
    interviewLevel?: InterviewLevel;

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
