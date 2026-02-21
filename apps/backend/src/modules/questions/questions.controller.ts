import { Controller, Post, Param, UseGuards, Req } from '@nestjs/common';
import { QuestionsService } from './questions.service';
import { JwtAuthGuard } from '../identity/guards/jwt-auth.guard';

@UseGuards(JwtAuthGuard)
@Controller('sessions/:sessionId/questions')
export class QuestionsController {
    constructor(private readonly questionsService: QuestionsService) { }

    @Post('next')
    generateNextQuestion(@Param('sessionId') sessionId: string, @Req() req: any) {
        // Enforcing security: using token's userId
        return this.questionsService.generateNextQuestion(sessionId, req.user.userId);
    }
}
