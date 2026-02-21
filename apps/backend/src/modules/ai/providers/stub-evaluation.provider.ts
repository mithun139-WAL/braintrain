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

        // --- Behavioral timing signals ---
        const pressureScore = this.scorePressure(input.responseTimeMs);
        const thinkingDepthScore = this.scoreThinkingDepth(input.thinkingTimeMs);

        const overallScore = this.computeOverall({
            clarityScore,
            structureScore,
            depthScore,
            confidenceScore,
            communicationScore,
            hesitationScore,
            technicalScore,
            pressureScore,
            thinkingDepthScore,
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
            pressureScore,
            thinkingDepthScore,
            overallScore,
            explanation:
                `[Stub] Evaluated ${wordCount} words. ` +
                `Overall: ${overallScore.toFixed(1)}/100. ` +
                `Pressure: ${pressureScore.toFixed(0)}, Thinking Depth: ${thinkingDepthScore.toFixed(0)}.`,
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

    /**
     * Pressure score — derived from total response time.
     * Optimal range: 15–45 seconds. Very fast = rushed/stressed. Very slow = stuck.
     * Score is 0–100 where 100 = perfectly calm and composed.
     * null/0 → neutral 50.
     */
    private scorePressure(responseTimeMs?: number): number {
        if (!responseTimeMs) return 50;
        const seconds = responseTimeMs / 1000;

        if (seconds < 5) return 20;   // Extremely rushed
        if (seconds < 10) return 40;  // Rushed
        if (seconds < 15) return 60;  // Slightly fast
        if (seconds <= 45) return 85; // Ideal window
        if (seconds <= 90) return 65; // Slightly slow
        return 40;                    // Struggling / very slow
    }

    /**
     * Thinking depth score — derived from pre-answer thinking pause.
     * A short deliberate pause (4–12s) = composed, thoughtful.
     * No pause (<2s) = reactive. Very long (>20s) = stuck.
     * null/0 → neutral 50.
     */
    private scoreThinkingDepth(thinkingTimeMs?: number): number {
        if (!thinkingTimeMs) return 50;
        const seconds = thinkingTimeMs / 1000;

        if (seconds < 1) return 30;   // Reactive, no reflection
        if (seconds < 3) return 50;   // Minimal thinking
        if (seconds < 6) return 70;   // Good
        if (seconds <= 12) return 90; // Deliberate and composed (optimal)
        if (seconds <= 20) return 65; // Slightly long
        return 35;                    // Stuck / panicking
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
        pressureScore: number;
        thinkingDepthScore: number;
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
            pressureScore,
            thinkingDepthScore,
            questionType,
        } = params;

        const hesitationPenalty = hesitationScore * 0.08;
        // Behavioral signals contribute 5% each (10% total)
        const behavioralBonus = (pressureScore * 0.05) + (thinkingDepthScore * 0.05);

        if (questionType === 'technical' && technicalScore !== null) {
            return Math.max(
                0.18 * clarityScore +
                0.13 * structureScore +
                0.18 * depthScore +
                0.13 * confidenceScore +
                0.08 * communicationScore +
                0.18 * technicalScore -
                hesitationPenalty +
                behavioralBonus,
                0
            );
        }

        // Behavioral weighting — confidence and structure matter more
        return Math.max(
            0.18 * clarityScore +
            0.18 * structureScore +
            0.18 * depthScore +
            0.18 * confidenceScore +
            0.08 * communicationScore +
            0.08 * (100 - hesitationScore) +
            behavioralBonus,
            0
        );
    }
}
