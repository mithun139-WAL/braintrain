import { Module } from '@nestjs/common';
import { QuestionsController } from './questions.controller';
import { QuestionsService } from './questions.service';
import { PrismaModule } from '../../prisma/prisma.module';
import { AdaptiveModule } from '../adaptive/adaptive.module';
import { QuestionBankModule } from '../question-bank/question-bank.module';
import { AIModule } from '../ai/ai.module';

@Module({
    imports: [PrismaModule, AdaptiveModule, QuestionBankModule, AIModule],
    controllers: [QuestionsController],
    providers: [QuestionsService],
    exports: [QuestionsService],
})
export class QuestionsModule { }
