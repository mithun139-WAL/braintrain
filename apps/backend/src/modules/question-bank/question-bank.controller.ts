import { Body, Controller, Get, Param, Post, Query, Req, UseGuards } from '@nestjs/common';
import { QuestionBankService } from './question-bank.service';
import { CreateQuestionBankDto } from './dto/create-question-bank.dto';
import { JwtAuthGuard } from '../identity/guards/jwt-auth.guard';
import { DifficultyLevel } from '@prisma/client';

@UseGuards(JwtAuthGuard)
@Controller('question-bank')
export class QuestionBankController {
    constructor(private readonly questionBankService: QuestionBankService) { }

    @Post()
    createQuestion(@Body() dto: CreateQuestionBankDto, @Req() req: any) {
        return this.questionBankService.createQuestion(dto, req.user.userId);
    }

    @Get()
    listQuestions(
        @Req() req: any,
        @Query('topicId') topicId: string,
        @Query('difficulty') difficulty?: DifficultyLevel,
    ) {
        if (!topicId) {
            return { message: 'topicId query param is required', data: [] };
        }
        return this.questionBankService.listQuestions(topicId, difficulty, req.user.userId);
    }

    @Get(':id')
    getById(@Param('id') id: string) {
        return this.questionBankService.getById(id);
    }
}
