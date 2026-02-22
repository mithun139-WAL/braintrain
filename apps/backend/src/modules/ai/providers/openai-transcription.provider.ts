import { Injectable, Logger } from '@nestjs/common';
import OpenAI, { toFile } from 'openai';
import * as https from 'https';
import * as http from 'http';
import { Buffer } from 'buffer';
import * as path from 'path';
import {
    AudioTranscriptionProvider,
    TranscriptionResult,
} from '../interfaces/audio-transcription-provider.interface';

/**
 * Whisper-1 pricing: $0.006 per minute (as of 2024-11)
 * We approximate: $0.0001 per second of audio.
 */
const WHISPER_COST_PER_SECOND_USD = 0.0001;

/**
 * Whisper's max file size (25 MB). Reject before attempting API call.
 */
const MAX_AUDIO_BYTES = 25 * 1024 * 1024;

/**
 * Supported audio MIME types by Whisper API.
 * Derived from extension since we receive a URL, not a browser File object.
 */
const EXTENSION_TO_MIME: Record<string, string> = {
    mp3: 'audio/mpeg',
    mp4: 'audio/mp4',
    m4a: 'audio/mp4',
    wav: 'audio/wav',
    webm: 'audio/webm',
    ogg: 'audio/ogg',
    flac: 'audio/flac',
    mpeg: 'audio/mpeg',
    mpga: 'audio/mpeg',
};

/**
 * OpenAITranscriptionProvider — Whisper-1 integration via the OpenAI SDK.
 *
 * Design decisions:
 *  - Downloads audio buffer from the provided URL (works with S3 presigned URLs)
 *  - Uses `toFile()` from openai SDK to construct a correct multipart upload
 *  - Returns empty string on failure (never throws) — evaluation still runs
 *    using the candidate's typed answerText if available
 *  - Extracts duration from Whisper's verbose_json response for cost tracking
 *  - Whisper is language-agnostic by default (auto-detects)
 *
 * Injection token: AI_TRANSCRIPTION_PROVIDER
 */
@Injectable()
export class OpenAITranscriptionProvider implements AudioTranscriptionProvider {
    private readonly logger = new Logger(OpenAITranscriptionProvider.name);
    private readonly client: OpenAI;

    constructor() {
        if (!process.env.OPENAI_API_KEY) {
            throw new Error('OPENAI_API_KEY is required for OpenAITranscriptionProvider');
        }
        this.client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    }

    async transcribe(audioUrl: string): Promise<TranscriptionResult> {
        try {
            // 1. Download the audio bytes
            const { buffer, filename, mimeType } = await this.fetchAudioBuffer(audioUrl);

            // 2. Safety check: reject oversized files before calling Whisper
            if (buffer.length > MAX_AUDIO_BYTES) {
                this.logger.warn(
                    `Audio at ${audioUrl} exceeds 25MB (${(buffer.length / 1024 / 1024).toFixed(1)}MB) — skipping transcription`,
                );
                return this.emptyResult('whisper-1-skipped-too-large');
            }

            // 3. Build the multipart file object Whisper expects
            const file = await toFile(buffer, filename, { type: mimeType });

            // 4. Call Whisper API with verbose_json for duration
            const response = await this.client.audio.transcriptions.create({
                model: 'whisper-1',
                file,
                response_format: 'verbose_json',
                language: undefined, // auto-detect
            });

            const text = (response as any).text ?? '';
            const durationSeconds = (response as any).duration ?? null;
            const estimatedCostUsd = durationSeconds !== null
                ? parseFloat((durationSeconds * WHISPER_COST_PER_SECOND_USD).toFixed(6))
                : null;

            this.logger.log(
                `Transcribed ${audioUrl} | ` +
                `${durationSeconds?.toFixed(1) ?? '?'}s | ` +
                `${text.split(/\s+/).filter(Boolean).length} words | ` +
                `~$${estimatedCostUsd?.toFixed(6) ?? '?'}`,
            );

            return {
                text,
                durationSeconds,
                modelUsed: 'whisper-1',
                isStub: false,
                estimatedCostUsd,
            };
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            this.logger.error(`Transcription failed for ${audioUrl}: ${message}`);
            // Graceful degradation — never throw; evaluation continues with answerText only
            return this.emptyResult('whisper-1-error');
        }
    }

    /**
     * Download audio from a URL (http or https) and return as a Buffer.
     * Extracts filename and MIME type from the URL path.
     */
    private fetchAudioBuffer(audioUrl: string): Promise<{
        buffer: Buffer;
        filename: string;
        mimeType: string;
    }> {
        return new Promise((resolve, reject) => {
            const urlObj = new URL(audioUrl);
            const rawPathname = urlObj.pathname.split('?')[0]; // strip query params
            const basename = path.basename(rawPathname);
            const ext = path.extname(basename).replace('.', '').toLowerCase();
            const mimeType = EXTENSION_TO_MIME[ext] ?? 'audio/mpeg';
            const filename = basename || `audio.${ext || 'mp3'}`;

            const protocol = urlObj.protocol === 'https:' ? https : http;

            protocol.get(audioUrl, (res) => {
                if (res.statusCode !== 200) {
                    reject(new Error(`HTTP ${res.statusCode} fetching audio from ${audioUrl}`));
                    return;
                }

                const chunks: Buffer[] = [];
                res.on('data', (chunk: Buffer) => chunks.push(chunk));
                res.on('end', () => resolve({ buffer: Buffer.concat(chunks), filename, mimeType }));
                res.on('error', reject);
            }).on('error', reject);
        });
    }

    private emptyResult(modelUsed: string): TranscriptionResult {
        return {
            text: '',
            durationSeconds: null,
            modelUsed,
            isStub: false,
            estimatedCostUsd: null,
        };
    }
}
