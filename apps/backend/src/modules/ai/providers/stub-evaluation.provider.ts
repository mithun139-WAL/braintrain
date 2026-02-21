import { Injectable } from '@nestjs/common';
import { AnswerEvaluationProvider } from '../interfaces/answer-evaluation-provider.interface';
import { EvaluationInput } from '../interfaces/evaluation-input.interface';
import { PerformanceSignal } from '../interfaces/performance-signal.interface';

/**
 * StubEvaluationProvider
 *
 * A deterministic, zero-cost implementation of AnswerEvaluationProvider.
 * Used in development and testing before real LLM integration.
 *
 * Scoring logic is based on simple heuristics so the pipeline produces
 * plausible, varied output without any external API call.
 */
@Injectable()
export class StubEvaluationProvider implements AnswerEvaluationProvider {
    async evaluate(input: EvaluationInput): Promise<PerformanceSignal> {
        const text = input.text ?? '';
        const wordCount = text.trim().split(/\s+/).filter(Boolean).length;

        // --- Deterministic heuristics ---
        const clarityScore = this.scoreClarity(text, wordCount);
        const structureScore = this.scoreStructure(text);
        const depthScore = this.scoreDepth(wordCount);
        const confidenceScore = this.scoreConfidence(text);
        const communicationScore = this.scoreCommunication(text, wordCount);
        const hesitationScore = this.scoreHesitation(text);
        const technicalScore = input.questionType === 'technical'
            ? this.scoreTechnical(text)
            : null;

        const overallScore = this.computeOverall({
            clarityScore,
            structureScore,
            depthScore,
            confidenceScore,
            communicationScore,
            hesitationScore,
            technicalScore,
            questionType: input.questionType,
        });

        return {
            clarityScore,
            structureScore,
            depthScore,
            confidenceScore,
            communicationScore,
            hesitationScore,
            technicalScore,
            overallScore,
            explanation:
                `[Stub] Evaluated ${wordCount} words. ` +
                `Overall: ${overallScore.toFixed(1)}/100.`,
        };
    }

    // ─── Heuristic Scorers ───────────────────────────────────────────────────

    /** Clarity: penalise very short or extremely long responses */
    private scoreClarity(text: string, wordCount: number): number {
        if (wordCount < 10) return 30;
        if (wordCount < 30) return 55;
        if (wordCount < 200) return 75;
        return 65; // Penalise rambling
    }

    /** Structure: looks for STAR-like transition markers */
    private scoreStructure(text: string): number {
        const markers = ['situation', 'task', 'action', 'result', 'because', 'therefore', 'finally'];
        const found = markers.filter(m => text.toLowerCase().includes(m)).length;
        // Base of 30: zero structural markers = genuinely unstructured answer
        // Each keyword adds +10, cap at 100
        return Math.min(30 + found * 10, 100);
    }

    /** Depth: based on word count — more content = more depth (up to a ceiling) */
    private scoreDepth(wordCount: number): number {
        if (wordCount < 20) return 25;
        if (wordCount < 80) return 55;
        if (wordCount < 200) return 80;
        return 90;
    }

    /** Confidence: penalises hedging phrases */
    private scoreConfidence(text: string): number {
        const hedges = ['i think', 'i guess', 'maybe', 'i\'m not sure', 'kind of', 'sort of'];
        const lc = text.toLowerCase();
        const count = hedges.filter(h => lc.includes(h)).length;
        return Math.max(80 - count * 10, 30);
    }

    /** Communication: penalises filler words */
    private scoreCommunication(text: string, wordCount: number): number {
        const fillers = ['um', 'uh', 'like', 'you know', 'basically', 'literally'];
        const lc = text.toLowerCase();
        const fillerCount = fillers.reduce((acc, f) => {
            const matches = lc.match(new RegExp(`\\b${f}\\b`, 'g'));
            return acc + (matches?.length ?? 0);
        }, 0);
        const density = wordCount > 0 ? fillerCount / wordCount : 0;
        return Math.max(90 - density * 200, 20);
    }

    /**
     * Hesitation: deterministic count of filler words + ellipsis patterns.
     * Lower is better — 0 means no hesitation detected.
     */
    private scoreHesitation(text: string): number {
        const fillers = ['um', 'uh', 'er', 'hmm'];
        const lc = text.toLowerCase();
        const fillerCount = fillers.reduce((acc, f) => {
            const matches = lc.match(new RegExp(`\\b${f}\\b`, 'g'));
            return acc + (matches?.length ?? 0);
        }, 0);
        const ellipsisCount = (text.match(/\.\.\./g) || []).length;
        return Math.min((fillerCount + ellipsisCount) * 15, 100);
    }

    /** Technical: presence of domain-specific vocabulary (naive proxy) */
    private scoreTechnical(text: string): number {
        const techTerms = ['algorithm', 'complexity', 'database', 'query', 'api', 'async', 'cache', 'index', 'scaling'];
        const lc = text.toLowerCase();
        const found = techTerms.filter(t => lc.includes(t)).length;
        return Math.min(40 + found * 8, 100);
    }

    // ─── Weighted Aggregation ────────────────────────────────────────────────

    private computeOverall(params: {
        clarityScore: number;
        structureScore: number;
        depthScore: number;
        confidenceScore: number;
        communicationScore: number;
        hesitationScore: number;
        technicalScore: number | null;
        questionType: 'behavioral' | 'technical';
    }): number {
        const {
            clarityScore,
            structureScore,
            depthScore,
            confidenceScore,
            communicationScore,
            hesitationScore,
            technicalScore,
            questionType,
        } = params;

        // Hesitation is an inverse signal — high hesitation lowers confidence
        const hesitationPenalty = hesitationScore * 0.10;

        if (questionType === 'technical' && technicalScore !== null) {
            // Technical weighting
            return Math.max(
                0.20 * clarityScore +
                0.15 * structureScore +
                0.20 * depthScore +
                0.15 * confidenceScore +
                0.10 * communicationScore +
                0.20 * technicalScore -
                hesitationPenalty,
                0
            );
        }

        // Behavioral weighting — confidence and structure matter more
        return Math.max(
            0.20 * clarityScore +
            0.20 * structureScore +
            0.20 * depthScore +
            0.20 * confidenceScore +
            0.10 * communicationScore +
            0.10 * (100 - hesitationScore), // treat low-hesitation as positive
            0
        );
    }
}
