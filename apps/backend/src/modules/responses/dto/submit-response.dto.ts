import { IsNotEmpty, IsString, IsOptional, IsInt, Min } from 'class-validator';

export class SubmitResponseDto {
    @IsNotEmpty()
    @IsString()
    answerText!: string;

    @IsOptional()
    @IsString()
    audioUrl?: string;

    @IsNotEmpty()
    @IsInt()
    @Min(0)
    responseTimeMs!: number;

    @IsNotEmpty()
    @IsInt()
    @Min(0)
    thinkingTimeMs!: number;
}
