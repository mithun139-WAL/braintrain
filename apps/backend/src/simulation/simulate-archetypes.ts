/**
 * simulate-archetypes.ts
 *
 * Standalone simulation of the evaluation + adaptive engine pipeline.
 * No HTTP, no DB, no NestJS — pure logic.
 *
 * Run with:
 *   npx ts-node --project tsconfig.json src/simulation/simulate-archetypes.ts
 *
 * Purpose:
 *   Validate that adaptive difficulty transitions feel human before
 *   wiring in OpenAI. Tune INCREASE_ABOVE / DECREASE_BELOW here.
 */

// ─── Inline types (mirrors the real interfaces) ──────────────────────────────

type DifficultyLevel = 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED';
type QuestionType = 'behavioral' | 'technical';

interface EvaluationInput {
    question: string;
    text?: string;
    questionType: QuestionType;
    difficulty: DifficultyLevel;
}

interface PerformanceSignal {
    clarityScore: number;
    structureScore: number;
    depthScore: number;
    confidenceScore: number;
    communicationScore: number;
    hesitationScore: number;
    technicalScore: number | null;
    overallScore: number;
    explanation: string;
}

// ─── Adaptive thresholds (mirrors adaptive-engine.service.ts) ────────────────
const INCREASE_ABOVE = 72;  // was 75 — strong candidates no longer stall at the boundary
const DECREASE_BELOW = 55;  // was 50 — catches genuinely weak performers (~52 avg)
const MIN_SCORED_RESPONSES = 2;

// ─── Inline Stub Evaluator (mirrors stub-evaluation.provider.ts) ─────────────

function scoreClarity(_text: string, wordCount: number): number {
    if (wordCount < 10) return 30;
    if (wordCount < 30) return 55;
    if (wordCount < 200) return 75;
    return 65;
}

function scoreStructure(text: string): number {
    const markers = ['situation', 'task', 'action', 'result', 'because', 'therefore', 'finally'];
    const found = markers.filter(m => text.toLowerCase().includes(m)).length;
    // Base 30 (was 40): zero structural markers = genuinely unstructured answer
    return Math.min(30 + found * 10, 100);
}

function scoreDepth(wordCount: number): number {
    if (wordCount < 20) return 25;
    if (wordCount < 80) return 55;
    if (wordCount < 200) return 80;
    return 90;
}

function scoreConfidence(text: string): number {
    const hedges = ["i think", "i guess", "maybe", "i'm not sure", "kind of", "sort of"];
    const lc = text.toLowerCase();
    const count = hedges.filter(h => lc.includes(h)).length;
    return Math.max(80 - count * 10, 30);
}

function scoreCommunication(text: string, wordCount: number): number {
    const fillers = ['um', 'uh', 'like', 'you know', 'basically', 'literally'];
    const lc = text.toLowerCase();
    const fillerCount = fillers.reduce((acc, f) => {
        const matches = lc.match(new RegExp(`\\b${f}\\b`, 'g'));
        return acc + (matches?.length ?? 0);
    }, 0);
    const density = wordCount > 0 ? fillerCount / wordCount : 0;
    return Math.max(90 - density * 200, 20);
}

function scoreHesitation(text: string): number {
    const fillers = ['um', 'uh', 'er', 'hmm'];
    const lc = text.toLowerCase();
    const fillerCount = fillers.reduce((acc, f) => {
        const matches = lc.match(new RegExp(`\\b${f}\\b`, 'g'));
        return acc + (matches?.length ?? 0);
    }, 0);
    const ellipsisCount = (text.match(/\.\.\./g) || []).length;
    return Math.min((fillerCount + ellipsisCount) * 15, 100);
}

function computeOverall(
    clarityScore: number, structureScore: number, depthScore: number,
    confidenceScore: number, communicationScore: number, hesitationScore: number,
    technicalScore: number | null, questionType: QuestionType,
): number {
    const hesitationPenalty = hesitationScore * 0.10;
    if (questionType === 'technical' && technicalScore !== null) {
        return Math.max(
            0.20 * clarityScore + 0.15 * structureScore + 0.20 * depthScore +
            0.15 * confidenceScore + 0.10 * communicationScore +
            0.20 * technicalScore - hesitationPenalty, 0
        );
    }
    return Math.max(
        0.20 * clarityScore + 0.20 * structureScore + 0.20 * depthScore +
        0.20 * confidenceScore + 0.10 * communicationScore +
        0.10 * (100 - hesitationScore), 0
    );
}

function evaluate(input: EvaluationInput): PerformanceSignal {
    const text = input.text ?? '';
    const wordCount = text.trim().split(/\s+/).filter(Boolean).length;
    const clarityScore = scoreClarity(text, wordCount);
    const structureScore = scoreStructure(text);
    const depthScore = scoreDepth(wordCount);
    const confidenceScore = scoreConfidence(text);
    const communicationScore = scoreCommunication(text, wordCount);
    const hesitationScore = scoreHesitation(text);
    const technicalScore = input.questionType === 'technical' ? 40 : null;
    const overallScore = computeOverall(
        clarityScore, structureScore, depthScore, confidenceScore,
        communicationScore, hesitationScore, technicalScore, input.questionType
    );
    return {
        clarityScore, structureScore, depthScore, confidenceScore,
        communicationScore, hesitationScore, technicalScore, overallScore,
        explanation: `${wordCount}w → overall ${overallScore.toFixed(1)}`
    };
}

// ─── Adaptive Engine (mirrors adaptive-engine.service.ts) ────────────────────

function nextDifficulty(current: DifficultyLevel, signals: PerformanceSignal[]): DifficultyLevel {
    if (signals.length < MIN_SCORED_RESPONSES) return current;
    const avg = signals.slice(-3).reduce((s, r) => s + r.overallScore, 0) /
        Math.min(signals.length, 3);
    if (avg > INCREASE_ABOVE) return increase(current);
    if (avg < DECREASE_BELOW) return decrease(current);
    return current;
}

function increase(d: DifficultyLevel): DifficultyLevel {
    if (d === 'BEGINNER') return 'INTERMEDIATE';
    if (d === 'INTERMEDIATE') return 'ADVANCED';
    return 'ADVANCED';
}
function decrease(d: DifficultyLevel): DifficultyLevel {
    if (d === 'ADVANCED') return 'INTERMEDIATE';
    if (d === 'INTERMEDIATE') return 'BEGINNER';
    return 'BEGINNER';
}

// ─── Candidate Archetypes ─────────────────────────────────────────────────────

/**
 * Each archetype provides 5 answers representing their natural voice.
 * Answer style is intentionally illustrative — these are the kinds of
 * texts the stub's heuristics respond to.
 */

const ARCHETYPES: Record<string, string[]> = {

    // ── STRONG CANDIDATE ──────────────────────────────────────────────────────
    // Long, STAR-structured, zero hedges, no fillers
    '🟢 Strong Candidate': [
        `In my previous role the situation was that our team had a critical production outage. 
         My task was to coordinate incident response across three squads. 
         The action I took was immediately setting up a war room and assigning ownership by domain. 
         As a result, we restored service in 47 minutes, well below our 2-hour SLA. 
         That experience fundamentally changed how I think about on-call ownership.`,

        `The situation was a product decision that I disagreed with strongly. 
         My task was to raise concerns constructively without escalating tension. 
         The action I took was preparing a short written brief with data, not opinion. 
         The result was the team agreed to a two-week experiment before committing. 
         I learned that structured disagreement is more effective than emotional pushback.`,

        `The situation was onboarding a team of five new engineers under a tight deadline. 
         My task was to deliver meaningful ramp-up without slowing the team velocity. 
         Because I had done this before, I created a structured 30-60-90 day ramp plan. 
         Finally, all five engineers were shipping independently within six weeks.`,

        `The task was to reduce API latency by 40 percent for our highest-traffic endpoint. 
         The action I took was profiling the call stack first, which revealed unnecessary 
         N+1 query patterns. I introduced a dataloader layer and the result was 
         a 58 percent latency reduction — exceeding the target.`,

        `To give you the full situation: our engineering culture had no feedback rituals. 
         My task was to introduce one that people would actually use. 
         I ran three one-on-one interviews first to understand blockers. 
         As a result, we shipped a lightweight async feedback loop that saw 80 percent adoption.`,
    ],

    // ── STRUGGLING CANDIDATE ─────────────────────────────────────────────────
    // Short, hedged, lots of fillers, no structure markers
    '🔴 Struggling Candidate': [
        `Um, yeah I think I once helped the team, like, with a bug or something. 
         I'm not sure exactly. It was kind of a tough situation I guess.`,

        `Uh, I maybe led a project? I'm not sure. Like, everyone helped so it 
         wasn't really just me. I think it went okay but I can't remember the result.`,

        `I guess I handled conflict by, um, just letting it go. Maybe talk to someone. 
         I'm not sure if that's the right answer.`,

        `Um. Basically I just did what I was told. I kind of followed the process. 
         I think it worked out? But yeah I don't know.`,

        `I think the biggest challenge was... um... like, I'm not sure. Maybe time management? 
         I kind of struggle with that. I guess I try to make checklists or something.`,
    ],

    // ── INCONSISTENT CANDIDATE ───────────────────────────────────────────────
    // Alternates between strong and weak — tests that the engine doesn't over-react
    '🟡 Inconsistent Candidate': [
        // Strong Q1
        `The situation was a tight sprint with conflicting priorities. My task was to 
         triage and protect the team from scope creep. The action I took was a 
         structured priority matrix reviewed with the product lead. 
         As a result, we shipped the core features on time.`,

        // Weak Q2
        `Um, yeah, I think I once, like, tried to improve something. 
         I'm not sure it worked. Kind of hard to say.`,

        // Strong Q3
        `The task was to migrate a legacy monolith service to microservices without downtime. 
         The action was the strangler fig pattern — because it let us route traffic gradually. 
         Finally, after six weeks, the legacy service handled zero traffic and was decommissioned.`,

        // Weak Q4
        `I maybe handled a disagreement once. I'm not sure. 
         I kind of just, um, let it go I guess.`,

        // Medium Q5
        `I worked on a feature that improved dashboard load time. 
         I profiled the frontend, found unnecessary renders, and fixed them. 
         The load time dropped noticeably and users were happy about it.`,
    ],
};

// ─── Simulation Runner ───────────────────────────────────────────────────────

const QUESTION = 'Tell me about a time you demonstrated leadership.';
const COL = {
    reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
    green: '\x1b[32m', red: '\x1b[31m', yellow: '\x1b[33m', cyan: '\x1b[36m'
};

function scoreBar(score: number, width = 20): string {
    const filled = Math.round((score / 100) * width);
    const color = score >= 70 ? COL.green : score >= 50 ? COL.yellow : COL.red;
    return color + '█'.repeat(filled) + COL.dim + '░'.repeat(width - filled) + COL.reset;
}

function difficultyLabel(d: DifficultyLevel): string {
    if (d === 'ADVANCED') return COL.red + 'ADVANCED' + COL.reset;
    if (d === 'INTERMEDIATE') return COL.yellow + 'INTERMEDIATE' + COL.reset;
    return COL.green + 'BEGINNER' + COL.reset;
}

function divider(char = '─', len = 90): string { return COL.dim + char.repeat(len) + COL.reset; }

console.log('\n' + divider('═'));
console.log(COL.bold + '  BRAINTRAIN — Adaptive Engine Simulation' + COL.reset);
console.log(COL.dim + '  Thresholds: increase > ' + INCREASE_ABOVE + '  |  decrease < ' + DECREASE_BELOW +
    '  |  min scored responses: ' + MIN_SCORED_RESPONSES + COL.reset);
console.log(divider('═'));

for (const [archetype, answers] of Object.entries(ARCHETYPES)) {
    console.log('\n' + divider());
    console.log(COL.bold + '  ' + archetype + COL.reset);
    console.log(divider());

    let currentDifficulty: DifficultyLevel = 'BEGINNER';
    const signals: PerformanceSignal[] = [];
    const transitions: string[] = [];

    for (let i = 0; i < answers.length; i++) {
        const signal = evaluate({
            question: QUESTION, text: answers[i],
            questionType: 'behavioral', difficulty: currentDifficulty
        });
        signals.push(signal);

        const prevDifficulty = currentDifficulty;
        currentDifficulty = nextDifficulty(currentDifficulty, signals);

        const transition = prevDifficulty !== currentDifficulty
            ? ` → ${difficultyLabel(currentDifficulty)}`
            : '';

        if (transition) transitions.push(`Q${i + 1}: ${prevDifficulty} → ${currentDifficulty}`);

        console.log(`\n  Q${i + 1}  [${difficultyLabel(prevDifficulty)}]${transition}`);
        console.log(`  ${COL.dim}Answer: "${answers[i].trim().slice(0, 70)}..."${COL.reset}`);
        console.log(`  ${'─'.repeat(55)}`);
        console.log(`  Clarity      ${scoreBar(signal.clarityScore)}  ${signal.clarityScore.toFixed(0).padStart(3)}`);
        console.log(`  Structure    ${scoreBar(signal.structureScore)}  ${signal.structureScore.toFixed(0).padStart(3)}`);
        console.log(`  Depth        ${scoreBar(signal.depthScore)}  ${signal.depthScore.toFixed(0).padStart(3)}`);
        console.log(`  Confidence   ${scoreBar(signal.confidenceScore)}  ${signal.confidenceScore.toFixed(0).padStart(3)}`);
        console.log(`  Comm.        ${scoreBar(signal.communicationScore)}  ${signal.communicationScore.toFixed(0).padStart(3)}`);
        console.log(`  Hesitation↓  ${scoreBar(signal.hesitationScore)}  ${signal.hesitationScore.toFixed(0).padStart(3)}`);
        console.log(`  ${COL.bold}Overall      ${scoreBar(signal.overallScore)}  ${signal.overallScore.toFixed(1).padStart(5)}${COL.reset}`);

        // Rolling average notice
        if (signals.length >= MIN_SCORED_RESPONSES) {
            const window = signals.slice(-3);
            const rollingAvg = window.reduce((s, r) => s + r.overallScore, 0) / window.length;
            const signal3 = rollingAvg > INCREASE_ABOVE ? COL.green + '↑ increase triggered' :
                rollingAvg < DECREASE_BELOW ? COL.red + '↓ decrease triggered' :
                    COL.dim + '→ holding';
            console.log(`  ${COL.dim}Rolling avg (last ${window.length}): ${rollingAvg.toFixed(1)} — ${signal3}${COL.reset}`);
        }
    }

    // ── Summary ──
    const finalAvg = signals.reduce((s, r) => s + r.overallScore, 0) / signals.length;
    console.log(`\n  ${divider('─', 55)}`);
    console.log(`  ${COL.bold}Session Average Overall: ${finalAvg.toFixed(1)}/100${COL.reset}`);
    console.log(`  Final Difficulty: ${difficultyLabel(currentDifficulty)}`);
    if (transitions.length) {
        console.log(`  Difficulty Transitions: ${transitions.join(' | ')}`);
    } else {
        console.log(`  ${COL.dim}No difficulty transitions occurred${COL.reset}`);
    }
}

// ─── Cross-Archetype Comparison Table ────────────────────────────────────────

console.log('\n\n' + divider('═'));
console.log(COL.bold + '  COMPARISON SUMMARY' + COL.reset);
console.log(divider('═'));
console.log(COL.dim + `  ${'Archetype'.padEnd(30)} ${'Avg Overall'.padEnd(14)} ${'Final Difficulty'.padEnd(18)} Transitions` + COL.reset);
console.log(divider());

for (const [archetype, answers] of Object.entries(ARCHETYPES)) {
    let currentDifficulty: DifficultyLevel = 'BEGINNER';
    const signals: PerformanceSignal[] = [];
    let transitionCount = 0;

    for (const answer of answers) {
        const signal = evaluate({
            question: QUESTION, text: answer,
            questionType: 'behavioral', difficulty: currentDifficulty
        });
        signals.push(signal);
        const prev: DifficultyLevel = currentDifficulty;
        currentDifficulty = nextDifficulty(currentDifficulty, signals);
        if (prev !== currentDifficulty) transitionCount++;
    }

    const avg = signals.reduce((s, r) => s + r.overallScore, 0) / signals.length;
    const label = archetype.replace(/[^\x20-\x7E]/g, '').trim().slice(0, 28);
    console.log(`  ${label.padEnd(30)} ${avg.toFixed(1).padEnd(14)} ${currentDifficulty.padEnd(18)} ${transitionCount} transition(s)`);
}

console.log('\n' + divider('═') + '\n');
