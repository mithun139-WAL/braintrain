import { Body, Controller, Post } from '@nestjs/common';
import { IdentityService } from './identity.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { VerifyOtpDto } from './dto/verify-otp.dto';
import { GoogleLoginDto } from './dto/google-login.dto';

@Controller('identity')
export class IdentityController {
    constructor(private readonly identityService: IdentityService) { }

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
}
