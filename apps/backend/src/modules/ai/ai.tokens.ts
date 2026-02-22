/**
 * DI injection token for the AnswerEvaluationProvider.
 *
 * Usage in providers array:
 *   { provide: AI_EVALUATION_PROVIDER, useClass: StubEvaluationProvider }
 *
 * Usage in constructor:
 *   @Inject(AI_EVALUATION_PROVIDER) private readonly aiProvider: AnswerEvaluationProvider
 */
export const AI_EVALUATION_PROVIDER = 'AI_EVALUATION_PROVIDER';

/**
 * DI injection token for the QuestionGenerationProvider.
 *
 * Usage in providers array:
 *   { provide: AI_QUESTION_GENERATION_PROVIDER, useClass: StubQuestionGenerationProvider }
 *
 * Usage in constructor:
 *   @Inject(AI_QUESTION_GENERATION_PROVIDER) private readonly questionGen: QuestionGenerationProvider
 */
export const AI_QUESTION_GENERATION_PROVIDER = 'AI_QUESTION_GENERATION_PROVIDER';

/**
 * DI injection token for the AudioTranscriptionProvider.
 *
 * Usage in providers array:
 *   { provide: AI_TRANSCRIPTION_PROVIDER, useClass: OpenAITranscriptionProvider }
 *
 * Usage in constructor:
 *   @Inject(AI_TRANSCRIPTION_PROVIDER) private readonly transcription: AudioTranscriptionProvider
 */
export const AI_TRANSCRIPTION_PROVIDER = 'AI_TRANSCRIPTION_PROVIDER';
