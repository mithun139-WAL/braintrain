import { Module } from '@nestjs/common';
import { EvaluationJobService } from './evaluation-job.service';
import { PrismaModule } from '../../prisma/prisma.module';

@Module({
    imports: [PrismaModule],
    providers: [EvaluationJobService],
    exports: [EvaluationJobService],
})
export class EvaluationJobModule { }
