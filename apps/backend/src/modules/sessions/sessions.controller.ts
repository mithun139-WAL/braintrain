import { Controller, Post, Get, Param, Body, UseGuards, Req, Put, Query } from '@nestjs/common';
import { SessionsService } from './sessions.service';
import { CreateSessionDto } from './dto/create-session.dto';
import { ListSessionsDto } from './dto/list-sessions.dto';
import { JwtAuthGuard } from '../identity/guards/jwt-auth.guard';

@UseGuards(JwtAuthGuard)
@Controller('sessions')
export class SessionsController {
    constructor(private readonly sessionsService: SessionsService) { }

    @Post()
    createSession(@Body() dto: CreateSessionDto, @Req() req: any) {
        // Ignoring any userId passed in the body, trusting the JWT guard completely
        return this.sessionsService.createSession(dto, req.user.userId);
    }

    @Get()
    listSessions(@Req() req: any, @Query() query: ListSessionsDto) {
        return this.sessionsService.listSessions(req.user.userId, query);
    }

    @Get(':id')
    getSession(@Param('id') id: string, @Req() req: any) {
        return this.sessionsService.getSessionById(id, req.user.userId);
    }

    @Put(':id/start')
    startSession(@Param('id') id: string, @Req() req: any) {
        return this.sessionsService.startSession(id, req.user.userId);
    }

    @Put(':id/complete')
    completeSession(@Param('id') id: string, @Req() req: any) {
        return this.sessionsService.completeSession(id, req.user.userId);
    }

    @Get(':id/status')
    getSessionStatus(@Param('id') id: string, @Req() req: any) {
        return this.sessionsService.getSessionStatus(id, req.user.userId);
    }
}
