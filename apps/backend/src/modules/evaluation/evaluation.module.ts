import { Module } from '@nestjs/common';
import { EvaluationController } from './evaluation.controller';
import { PrismaModule } from '../../prisma/prisma.module';
import { EvaluationService } from './evaluation.service';
import { AIModule } from '../ai/ai.module';

@Module({
    imports: [PrismaModule, AIModule],
    controllers: [EvaluationController],
    providers: [EvaluationService],
    exports: [EvaluationService],
})
export class EvaluationModule { }
