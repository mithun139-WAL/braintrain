import { Module } from '@nestjs/common';
import { SessionsController } from './sessions.controller';
import { SessionsService } from './sessions.service';
import { PrismaModule } from '../../prisma/prisma.module';
import { EvaluationJobModule } from '../evaluation-job/evaluation-job.module';
import { UsageModule } from '../usage/usage.module';

@Module({
    imports: [PrismaModule, EvaluationJobModule, UsageModule],
    controllers: [SessionsController],
    providers: [SessionsService],
    exports: [SessionsService],
})
export class SessionsModule { }
