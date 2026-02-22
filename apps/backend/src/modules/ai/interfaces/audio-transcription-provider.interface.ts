/**
 * AudioTranscriptionProvider — abstraction for converting audio to text.
 *
 * Follows the same provider-pattern as AnswerEvaluationProvider:
 *   - Injection token: AI_TRANSCRIPTION_PROVIDER (see ai.tokens.ts)
 *   - Concrete implementations: OpenAITranscriptionProvider, StubTranscriptionProvider
 *   - Swap is env-driven: OPENAI_API_KEY set → OpenAI Whisper, absent → Stub
 *
 * The rest of the system only ever depends on this interface, never on a
 * specific provider class.
 */
export interface AudioTranscriptionProvider {
    /**
     * Download and transcribe the audio at the given URL.
     *
     * @param audioUrl  Publicly accessible URL (e.g., S3 presigned URL)
     *                  or a local file path during development.
     * @returns         Transcribed text (empty string if audio is silent or
     *                  if the provider cannot process it — never throws on
     *                  transcription failure, instead returns '').
     */
    transcribe(audioUrl: string): Promise<TranscriptionResult>;
}

export interface TranscriptionResult {
    /** Transcribed text — empty string if audio was silent or unprocessable */
    text: string;
    /** Duration of the audio clip in seconds (null if unavailable) */
    durationSeconds: number | null;
    /** Model used for transcription — for cost tracking and observability */
    modelUsed: string;
    /** Whether this result was produced by a stub (zero-cost) provider */
    isStub: boolean;
    /** Estimated cost in USD (null for stub) */
    estimatedCostUsd: number | null;
}
