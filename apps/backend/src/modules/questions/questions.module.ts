import { Module } from '@nestjs/common';
import { QuestionsController } from './questions.controller';
import { QuestionsService } from './questions.service';
import { PrismaModule } from '../../prisma/prisma.module';
import { AdaptiveModule } from '../adaptive/adaptive.module';

@Module({
    imports: [PrismaModule, AdaptiveModule],
    controllers: [QuestionsController],
    providers: [QuestionsService],
    exports: [QuestionsService],
})
export class QuestionsModule { }
