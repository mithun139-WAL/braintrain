import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ConfigModule } from '@nestjs/config';
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

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: `.env.${process.env.NODE_ENV || 'development'}`,
    }),
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
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule { }
