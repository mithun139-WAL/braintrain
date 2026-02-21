import { Module } from '@nestjs/common';
import { AdaptiveEngineService } from './adaptive-engine.service';
import { PrismaModule } from '../../prisma/prisma.module';

@Module({
    imports: [PrismaModule],
    providers: [AdaptiveEngineService],
    exports: [AdaptiveEngineService],
})
export class AdaptiveModule { }
