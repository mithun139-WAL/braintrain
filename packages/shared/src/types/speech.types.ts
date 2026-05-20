// Speech analysis types — Speech pattern analysis from transcribed text

export interface FillerWordOccurrence {
    word: string;
    count: number;
    percentage: number;             // percentage of total words
}

export interface SpeechAnalysisResult {
    wordCount: number;
    uniqueWordCount: number;
    vocabularyDiversityScore: number; // 0–100 (unique/total ratio)
    wordsPerMinute?: number;          // null if duration unknown
    avgSentenceLengthWords: number;
    fillerWords: FillerWordOccurrence[];
    fillerWordRate: number;           // filler words per 100 words
    confidenceMarkers: {
        assertive: string[];          // "I believe", "I know", "clearly"
        hedging: string[];            // "I think", "maybe", "sort of"
        assertiveCount: number;
        hedgingCount: number;
        confidenceRatio: number;      // assertive / (assertive + hedging)
    };
    structureIndicators: {
        hasOpening: boolean;
        hasConclusion: boolean;
        usesTransitions: boolean;
        starFormatDetected: boolean;  // Situation-Task-Action-Result
    };
    speechScore: number;              // 0–100 composite score
    insights: string[];               // human-readable behavioral insights
    recommendations: string[];        // actionable improvements
}
