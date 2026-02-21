import { Controller, Get, Post, Param, UseGuards, Req } from '@nestjs/common';
import { JwtAuthGuard } from '../identity/guards/jwt-auth.guard';
import { EvaluationService } from './evaluation.service';
import { SessionEvaluationResponseDto } from './dto/session-evaluation-response.dto';

@UseGuards(JwtAuthGuard)
@Controller('sessions/:sessionId/evaluation')
export class EvaluationController {
    constructor(private readonly evaluationService: EvaluationService) { }

    /**
     * POST /sessions/:sessionId/evaluation/analyze
     *
     * Triggers AI evaluation for a COMPLETED session.
     * Persists per-response scores, produces an aggregated EvaluationReport,
     * and transitions the session to ANALYZED.
     * Idempotent guard: throws 409 if already analyzed.
     */
    @Post('analyze')
    analyzeSession(
        @Param('sessionId') sessionId: string,
        @Req() req: any,
    ): Promise<SessionEvaluationResponseDto> {
        return this.evaluationService.analyzeSession(sessionId, req.user.userId);
    }

    /**
     * GET /sessions/:sessionId/evaluation
     *
     * Retrieves an existing evaluation report for a session.
     * Returns 404 if the session has not been analyzed yet.
     */
    @Get()
    getEvaluation(
        @Param('sessionId') sessionId: string,
        @Req() req: any,
    ): Promise<SessionEvaluationResponseDto> {
        return this.evaluationService.getEvaluation(sessionId, req.user.userId);
    }
}
