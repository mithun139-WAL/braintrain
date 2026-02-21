import { EvaluationReport, InterviewSession, QuestionInstance } from '@prisma/client';
import {
    SessionEvaluationResponseDto,
    EvaluationDimensionsDto,
    DifficultyProgressionDto,
} from './session-evaluation-response.dto';

type EvaluationReportWithSession = EvaluationReport & {
    session: InterviewSession & {
        questions: QuestionInstance[];
    };
};

/**
 * Maps a raw EvaluationReport (with its nested session + questions)
 * into the clean SessionEvaluationResponseDto.
 *
 * Kept as a pure function — no DI, no side effects — easy to unit test.
 */
export function toEvaluationResponseDto(
    report: EvaluationReportWithSession,
): SessionEvaluationResponseDto {
    const questions = report.session.questions ?? [];

    // ── Difficulty Progression ─────────────────────────────────────────────
    // Questions are ordered by sequenceOrder asc so first = earliest, last = latest
    const sorted = [...questions].sort((a, b) => a.sequenceOrder - b.sequenceOrder);
    const difficultyProgression: DifficultyProgressionDto = {
        startedAt: report.session.difficulty,        // Session base difficulty
        endedAt: sorted.at(-1)?.difficulty ?? report.session.difficulty,
    };

    // ── Dimensions ─────────────────────────────────────────────────────────
    const hesitationForDisplay = Math.max(0, 100 - report.hesitationScore);
    const dimensions: EvaluationDimensionsDto = {
        clarity: report.clarityScore,
        structure: report.structureScore,
        depth: report.depthScore,
        confidence: report.confidenceScore,
        communication: report.communicationScore,
        hesitation: hesitationForDisplay,   // Inverted: higher = better
        technical: report.technicalScore,
    };

    // ── Strengths: dimensions scoring ≥ 70 ────────────────────────────────
    const strengths = deriveStrengths(dimensions);

    // ── Improvements: flat list from improvementSuggestions JSON ──────────
    const rawSuggestions = report.improvementSuggestions as Record<string, string[]>;
    const improvements = Object.values(rawSuggestions).flat();

    return {
        sessionId: report.sessionId,
        overallScore: report.overallScore,
        summary: report.feedbackSummary,
        dimensions,
        strengths,
        improvements,
        difficultyProgression,
        evaluatedAt: report.createdAt.toISOString(),
    };
}

// ─── Helpers ────────────────────────────────────────────────────────────────

const STRENGTH_THRESHOLD = 70;

const DIMENSION_LABELS: Record<keyof EvaluationDimensionsDto, string> = {
    clarity: 'Clear and coherent communication',
    structure: 'Well-structured answers (STAR format)',
    depth: 'Strong depth and detail in responses',
    confidence: 'Confident and assertive delivery',
    communication: 'Fluent communication with minimal fillers',
    hesitation: 'Composed delivery with minimal hesitation',
    technical: 'Solid technical knowledge',
};

function deriveStrengths(dimensions: EvaluationDimensionsDto): string[] {
    return (Object.entries(dimensions) as [keyof EvaluationDimensionsDto, number | null][])
        .filter(([, score]) => score !== null && score >= STRENGTH_THRESHOLD)
        .map(([key]) => DIMENSION_LABELS[key]);
}
