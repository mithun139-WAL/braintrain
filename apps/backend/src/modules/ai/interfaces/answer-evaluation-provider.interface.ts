import { EvaluationInput } from './evaluation-input.interface';
import { PerformanceSignal } from './performance-signal.interface';

/**
 * AnswerEvaluationProvider — the core AI abstraction interface.
 *
 * Any concrete provider (stub, OpenAI, Anthropic, local LLM) must implement
 * this contract. The rest of the system only ever depends on this interface,
 * never on a specific provider class.
 *
 * Injection token: AI_EVALUATION_PROVIDER (see ai.tokens.ts)
 */
export interface AnswerEvaluationProvider {
    /**
     * Evaluate a single answer and return structured confidence signals.
     * Implementation may call an LLM, a local model, or return deterministic stubs.
     */
    evaluate(input: EvaluationInput): Promise<PerformanceSignal>;
}
