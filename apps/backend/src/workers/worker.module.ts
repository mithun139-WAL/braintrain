import { Module } from '@nestjs/common';
import { ScheduleModule } from '@nestjs/schedule';
import { EvaluationWorker } from './evaluation.worker';
import { EvaluationJobModule } from '../modules/evaluation-job/evaluation-job.module';
import { EvaluationModule } from '../modules/evaluation/evaluation.module';

@Module({
    imports: [
        ScheduleModule.forRoot(),
        EvaluationJobModule,
        EvaluationModule,
    ],
    providers: [EvaluationWorker],
})
export class WorkerModule { }
