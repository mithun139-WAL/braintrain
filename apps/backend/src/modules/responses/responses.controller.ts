import { Controller, Post, Param, Body, UseGuards, Req } from '@nestjs/common';
import { ResponsesService } from './responses.service';
import { SubmitResponseDto } from './dto/submit-response.dto';
import { JwtAuthGuard } from '../identity/guards/jwt-auth.guard';

@UseGuards(JwtAuthGuard)
@Controller('questions/:questionId/responses')
export class ResponsesController {
    constructor(private readonly responsesService: ResponsesService) { }

    @Post()
    submitResponse(
        @Param('questionId') questionId: string,
        @Body() dto: SubmitResponseDto,
        @Req() req: any
    ) {
        // Enforcing security: using token's userId securely
        return this.responsesService.submitResponse(questionId, req.user.userId, dto);
    }
}
