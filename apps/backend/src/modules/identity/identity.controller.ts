import { Body, Controller, Delete, Get, Param, Post, Put, Req, UseGuards } from '@nestjs/common';
import { IdentityService } from './identity.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { VerifyOtpDto } from './dto/verify-otp.dto';
import { GoogleLoginDto } from './dto/google-login.dto';
import { UpdateProfileDto } from './dto/update-profile.dto';
import { AddSkillPreferenceDto } from './dto/add-skill-preference.dto';
import { JwtAuthGuard } from './guards/jwt-auth.guard';

@Controller('identity')
export class IdentityController {
    constructor(private readonly identityService: IdentityService) { }

    // ── Auth (public) ─────────────────────────────────────────────────────────

    @Post('register')
    register(@Body() registerDto: RegisterDto) {
        return this.identityService.register(registerDto);
    }

    @Post('login')
    login(@Body() loginDto: LoginDto) {
        return this.identityService.login(loginDto);
    }

    @Post('request-otp')
    requestOtp(@Body('identifier') identifier: string) {
        return this.identityService.requestOtp(identifier);
    }

    @Post('verify-otp')
    verifyOtp(@Body() verifyOtpDto: VerifyOtpDto) {
        return this.identityService.verifyOtp(verifyOtpDto);
    }

    @Post('google')
    googleLogin(@Body() googleLoginDto: GoogleLoginDto) {
        return this.identityService.googleLogin(googleLoginDto);
    }

    // ── Profile (JWT protected) ───────────────────────────────────────────────

    @UseGuards(JwtAuthGuard)
    @Get('me')
    getProfile(@Req() req: any) {
        return this.identityService.getProfile(req.user.userId);
    }

    @UseGuards(JwtAuthGuard)
    @Put('me')
    updateProfile(@Req() req: any, @Body() dto: UpdateProfileDto) {
        return this.identityService.updateProfile(req.user.userId, dto);
    }

    // ── Skill Tags (JWT protected) ────────────────────────────────────────────

    @UseGuards(JwtAuthGuard)
    @Get('skill-tags')
    getSkillTags() {
        return this.identityService.getSkillTags();
    }

    // ── Skill Preferences (JWT protected) ────────────────────────────────────

    @UseGuards(JwtAuthGuard)
    @Post('me/skills')
    addSkillPreference(@Req() req: any, @Body() dto: AddSkillPreferenceDto) {
        return this.identityService.addSkillPreference(req.user.userId, dto);
    }

    @UseGuards(JwtAuthGuard)
    @Delete('me/skills/:skillTagId')
    removeSkillPreference(@Req() req: any, @Param('skillTagId') skillTagId: string) {
        return this.identityService.removeSkillPreference(req.user.userId, skillTagId);
    }
}
