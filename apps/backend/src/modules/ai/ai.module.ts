import { Module } from '@nestjs/common';
import { AI_EVALUATION_PROVIDER } from './ai.tokens';
import { StubEvaluationProvider } from './providers/stub-evaluation.provider';

/**
 * AIModule — owns the AnswerEvaluationProvider binding.
 *
 * To swap providers, change `useClass` here. No other module needs to change.
 * Future: read process.env.AI_PROVIDER to select OpenAI / Anthropic / local.
 */
@Module({
    providers: [
        {
            provide: AI_EVALUATION_PROVIDER,
            useClass: StubEvaluationProvider,
            // Future: useClass: process.env.AI_PROVIDER === 'openai'
            //   ? OpenAIEvaluationProvider
            //   : StubEvaluationProvider,
        },
    ],
    exports: [AI_EVALUATION_PROVIDER],
})
export class AIModule { }
