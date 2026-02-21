import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ConfigModule } from '@nestjs/config';
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';
import { PrismaModule } from './prisma/prisma.module';
import { IdentityModule } from './modules/identity/identity.module';
import { SessionsModule } from './modules/sessions/sessions.module';
import { QuestionsModule } from './modules/questions/questions.module';
import { ResponsesModule } from './modules/responses/responses.module';
import { EvaluationModule } from './modules/evaluation/evaluation.module';
import { AdaptiveModule } from './modules/adaptive/adaptive.module';
import { TopicsModule } from './modules/topics/topics.module';
import { QuestionBankModule } from './modules/question-bank/question-bank.module';
import { AnalyticsModule } from './modules/analytics/analytics.module';
import { EvaluationJobModule } from './modules/evaluation-job/evaluation-job.module';
import { UsageModule } from './modules/usage/usage.module';
import { WorkerModule } from './workers/worker.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: `.env.${process.env.NODE_ENV || 'development'}`,
    }),
    ThrottlerModule.forRoot([
      {
        name: 'global',
        ttl: 60000,   // 60 seconds window
        limit: 30,    // max 30 requests per IP per 60s (adjust per route if needed)
      },
    ]),
    PrismaModule,
    IdentityModule,
    SessionsModule,
    QuestionsModule,
    ResponsesModule,
    EvaluationModule,
    AdaptiveModule,
    TopicsModule,
    QuestionBankModule,
    AnalyticsModule,
    EvaluationJobModule,
    UsageModule,
    WorkerModule,
  ],
  controllers: [AppController],
  providers: [
    AppService,
    // Global rate limiter guard — applies to all routes
    { provide: APP_GUARD, useClass: ThrottlerGuard },
  ],
})
export class AppModule { }
