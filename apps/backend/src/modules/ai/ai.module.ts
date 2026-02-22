import { Logger, Module } from '@nestjs/common';
import { AI_EVALUATION_PROVIDER, AI_QUESTION_GENERATION_PROVIDER, AI_TRANSCRIPTION_PROVIDER } from './ai.tokens';
import { StubEvaluationProvider } from './providers/stub-evaluation.provider';
import { OpenAIEvaluationProvider } from './providers/openai-evaluation.provider';
import { StubQuestionGenerationProvider } from './providers/stub-question-generation.provider';
import { OpenAIQuestionGenerationProvider } from './providers/openai-question-generation.provider';
import { StubTranscriptionProvider } from './providers/stub-transcription.provider';
import { OpenAITranscriptionProvider } from './providers/openai-transcription.provider';
import { PrismaModule } from '../../prisma/prisma.module';

/**
 * AIModule — owns all AI provider bindings.
 *
 * Provider selection is fully env-driven:
 *   OPENAI_API_KEY set   → OpenAI providers (GPT-4o + Whisper)
 *   OPENAI_API_KEY unset → Stub providers (offline, zero cost)
 *
 * No code changes needed to swap — just set/unset OPENAI_API_KEY.
 */
const aiLogger = new Logger('AIModule');
const useOpenAI = !!process.env.OPENAI_API_KEY;
aiLogger.log(
    `AI Providers: ${useOpenAI ? 'OpenAI (GPT-4o-mini eval + Whisper-1 transcription)' : 'Stub (offline)'}`,
);

@Module({
    imports: [PrismaModule],
    providers: [
        StubEvaluationProvider,
        StubQuestionGenerationProvider,
        StubTranscriptionProvider,
        OpenAIEvaluationProvider,
        OpenAIQuestionGenerationProvider,
        OpenAITranscriptionProvider,
        {
            provide: AI_EVALUATION_PROVIDER,
            useClass: useOpenAI ? OpenAIEvaluationProvider : StubEvaluationProvider,
        },
        {
            provide: AI_QUESTION_GENERATION_PROVIDER,
            useClass: useOpenAI ? OpenAIQuestionGenerationProvider : StubQuestionGenerationProvider,
        },
        {
            provide: AI_TRANSCRIPTION_PROVIDER,
            useClass: useOpenAI ? OpenAITranscriptionProvider : StubTranscriptionProvider,
        },
    ],
    exports: [AI_EVALUATION_PROVIDER, AI_QUESTION_GENERATION_PROVIDER, AI_TRANSCRIPTION_PROVIDER],
})
export class AIModule { }
