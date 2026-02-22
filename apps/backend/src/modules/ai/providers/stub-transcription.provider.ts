import { Injectable, Logger } from '@nestjs/common';
import {
    AudioTranscriptionProvider,
    TranscriptionResult,
} from '../interfaces/audio-transcription-provider.interface';

/**
 * StubTranscriptionProvider — zero-cost fallback for audio transcription.
 *
 * Used when:
 *   - OPENAI_API_KEY is not set (offline / dev mode)
 *   - The real transcription provider fails and the system degrades gracefully
 *
 * Returns an empty transcription so the downstream evaluation pipeline can
 * still operate using whatever answerText the user submitted manually.
 */
@Injectable()
export class StubTranscriptionProvider implements AudioTranscriptionProvider {
    private readonly logger = new Logger(StubTranscriptionProvider.name);

    async transcribe(audioUrl: string): Promise<TranscriptionResult> {
        this.logger.debug(`[Stub] Skipping transcription for: ${audioUrl}`);
        return {
            text: '',
            durationSeconds: null,
            modelUsed: 'stub',
            isStub: true,
            estimatedCostUsd: null,
        };
    }
}
