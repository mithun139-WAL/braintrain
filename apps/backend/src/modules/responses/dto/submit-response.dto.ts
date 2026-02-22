import { IsString, IsOptional, IsInt, Min, ValidateIf, IsUrl } from 'class-validator';

/**
 * SubmitResponseDto — body for POST /questions/:questionId/responses
 *
 * Audio-first design:
 *   - answerText is optional (candidate may speak only, no typed text)
 *   - audioUrl is optional (candidate may type only, no recording)
 *   - At least one of the two MUST be provided (enforced in service layer)
 *   - Both may be provided simultaneously (typed backup for audio session)
 *
 * Audio transcription via Whisper runs asynchronously inside EvaluationService.
 * The transcribed text is merged with answerText (audio takes precedence when
 * both are present and transcription succeeds) before the LLM evaluation call.
 */
export class SubmitResponseDto {
    @IsOptional()
    @IsString()
    answerText?: string;

    @IsOptional()
    @IsString()
    @ValidateIf(o => !!o.audioUrl)
    audioUrl?: string;

    @IsInt()
    @Min(0)
    responseTimeMs!: number;

    @IsInt()
    @Min(0)
    thinkingTimeMs!: number;
}
