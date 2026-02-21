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
