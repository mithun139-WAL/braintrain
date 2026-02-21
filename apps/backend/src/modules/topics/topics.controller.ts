import { Body, Controller, Delete, Get, Param, Post, Req, UseGuards } from '@nestjs/common';
import { TopicsService } from './topics.service';
import { CreateTopicDto } from './dto/create-topic.dto';
import { JwtAuthGuard } from '../identity/guards/jwt-auth.guard';

@UseGuards(JwtAuthGuard)
@Controller('topics')
export class TopicsController {
    constructor(private readonly topicsService: TopicsService) { }

    @Post()
    createTopic(@Body() dto: CreateTopicDto, @Req() req: any) {
        return this.topicsService.createTopic(dto, req.user.userId);
    }

    @Get()
    listTopics(@Req() req: any) {
        return this.topicsService.listTopics(req.user.userId);
    }

    @Get(':id')
    getTopicById(@Param('id') id: string, @Req() req: any) {
        return this.topicsService.getTopicById(id, req.user.userId);
    }

    @Delete(':id')
    deleteTopic(@Param('id') id: string, @Req() req: any) {
        return this.topicsService.deleteTopic(id, req.user.userId);
    }
}
