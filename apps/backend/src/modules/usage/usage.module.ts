import { Module } from '@nestjs/common';
import { ScheduleModule } from '@nestjs/schedule';
import { UsageService } from './usage.service';
import { PrismaModule } from '../../prisma/prisma.module';

@Module({
    imports: [ScheduleModule.forRoot(), PrismaModule],
    providers: [UsageService],
    exports: [UsageService],
})
export class UsageModule { }
