import { BadRequestException, Injectable, NotFoundException, UnauthorizedException } from '@nestjs/common';
import { PrismaService } from '../../prisma/prisma.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { VerifyOtpDto } from './dto/verify-otp.dto';
import { GoogleLoginDto } from './dto/google-login.dto';
import { UpdateProfileDto } from './dto/update-profile.dto';
import { AddSkillPreferenceDto } from './dto/add-skill-preference.dto';
import * as bcrypt from 'bcrypt';
import { JwtService } from '@nestjs/jwt';
import { OAuth2Client } from 'google-auth-library';
import { ConfigService } from '@nestjs/config';
import { EmailService } from './providers/email.service';
import { SmsService } from './providers/sms.service';

@Injectable()
export class IdentityService {
    private googleClient: OAuth2Client;

    constructor(
        private readonly prisma: PrismaService,
        private readonly jwtService: JwtService,
        private readonly configService: ConfigService,
        private readonly emailService: EmailService,
        private readonly smsService: SmsService,
    ) {
        this.googleClient = new OAuth2Client(this.configService.get('GOOGLE_CLIENT_ID'));
    }

    async register(registerDto: RegisterDto) {
        const { email, phoneNumber, password, name } = registerDto;

        if (!email && !phoneNumber) {
            throw new BadRequestException('Email or phone number is required');
        }

        if (email) {
            const existingUser = await this.prisma.user.findFirst({ where: { email, deletedAt: null } });
            if (existingUser) throw new BadRequestException('Email already in use');
        }

        if (phoneNumber) {
            const existingUser = await this.prisma.user.findFirst({ where: { phoneNumber, deletedAt: null } });
            if (existingUser) throw new BadRequestException('Phone number already in use');
        }

        let passwordHash = null;
        if (password) {
            passwordHash = await bcrypt.hash(password, 10);
        }

        const user = await this.prisma.user.create({
            data: {
                email: email ?? null,
                phoneNumber: phoneNumber ?? null,
                passwordHash,
                displayName: name ?? null,
            },
        });

        return this.generateAuthResponse(user);
    }

    async login(loginDto: LoginDto) {
        const { email, phoneNumber, password } = loginDto;

        if (!email && !phoneNumber) {
            throw new BadRequestException('Email or phone number is required');
        }

        let user;
        if (email) {
            user = await this.prisma.user.findFirst({ where: { email, deletedAt: null } });
        } else if (phoneNumber) {
            user = await this.prisma.user.findFirst({ where: { phoneNumber, deletedAt: null } });
        }

        if (!user || !user.passwordHash) {
            throw new UnauthorizedException('Invalid credentials');
        }

        const isPasswordValid = await bcrypt.compare(password || '', user.passwordHash);
        if (!isPasswordValid) {
            throw new UnauthorizedException('Invalid credentials');
        }

        return this.generateAuthResponse(user);
    }

    async requestOtp(identifier: string) {
        // Rate Limiting: 1 OTP per 60 seconds
        const recentOtp = await this.prisma.otpCode.findFirst({
            where: {
                identifier,
                createdAt: { gt: new Date(Date.now() - 60 * 1000) }
            }
        });

        if (recentOtp) {
            throw new BadRequestException("Please wait before requesting another OTP");
        }

        // Generate a 6-digit OTP
        const code = Math.floor(100000 + Math.random() * 900000).toString();

        // Determine expiration based on channel type
        const isEmail = identifier.includes('@');
        const expirationMinutes = isEmail ? 2 : 1;
        const expiresAt = new Date(Date.now() + expirationMinutes * 60 * 1000);

        // Hash the OTP before storing for security
        const hashedCode = await bcrypt.hash(code, 10);

        // Check if user exists
        let user = await this.prisma.user.findFirst({
            where: {
                OR: [{ email: identifier }, { phoneNumber: identifier }],
                deletedAt: null,
            },
        });

        // Save OTP to database
        await this.prisma.otpCode.create({
            data: {
                identifier,
                code: hashedCode,
                expiresAt,
                userId: user ? user.id : null,
            },
        });

        // Send the OTP via SMS or Email service based on the identifier type
        if (identifier.includes('@')) {
            await this.emailService.sendOtp(identifier, code);
        } else {
            await this.smsService.sendOtp(identifier, code);
        }

        return { message: 'OTP sent successfully' };
    }

    async verifyOtp(verifyOtpDto: VerifyOtpDto) {
        const { identifier, code } = verifyOtpDto;

        const otpRecord = await this.prisma.otpCode.findFirst({
            where: {
                identifier,
                isUsed: false,
                expiresAt: { gt: new Date() }
            },
            orderBy: { createdAt: 'desc' },
        });

        if (!otpRecord) {
            throw new BadRequestException('Invalid or expired OTP');
        }

        const isCodeValid = await bcrypt.compare(code, otpRecord.code);
        if (!isCodeValid) {
            throw new BadRequestException('Invalid or expired OTP');
        }

        // Mark OTP as used
        await this.prisma.otpCode.update({
            where: { id: otpRecord.id },
            data: { isUsed: true },
        });

        // Find or create user
        let user = await this.prisma.user.findFirst({
            where: {
                OR: [{ email: identifier }, { phoneNumber: identifier }],
                deletedAt: null
            },
        });

        if (!user) {
            // Create new user if not exists
            const isEmail = identifier.includes('@');
            user = await this.prisma.user.create({
                data: {
                    email: isEmail ? identifier : null,
                    phoneNumber: !isEmail ? identifier : null,
                },
            });
        }

        return this.generateAuthResponse(user);
    }

    async googleLogin(googleLoginDto: GoogleLoginDto) {
        const { token } = googleLoginDto;
        try {
            const ticket = await this.googleClient.verifyIdToken({
                idToken: token,
                audience: this.configService.get('GOOGLE_CLIENT_ID'),
            });

            const payload = ticket.getPayload();
            if (!payload || !payload.email) {
                throw new BadRequestException('Invalid Google token');
            }

            const { email, sub: googleId, name, picture } = payload;

            let user = await this.prisma.user.findFirst({
                where: {
                    OR: [{ googleId }, { email }],
                    deletedAt: null,
                },
            });

            if (!user) {
                user = await this.prisma.user.create({
                    data: {
                        email,
                        googleId,
                        displayName: name ?? null,
                        avatarUrl: picture ?? null,
                    },
                });
            } else if (!user.googleId) {
                // Link google account to existing email user
                user = await this.prisma.user.update({
                    where: { id: user.id },
                    data: {
                        googleId,
                        displayName: user.displayName ?? name ?? null,
                        avatarUrl: user.avatarUrl ?? picture ?? null,
                    },
                });
            }

            return this.generateAuthResponse(user);
        } catch (error) {
            console.error(error);
            throw new UnauthorizedException('Google authentication failed');
        }
    }

    // ── Profile ──────────────────────────────────────────────────────────────

    async getProfile(userId: string) {
        const user = await this.prisma.user.findFirst({
            where: { id: userId, deletedAt: null },
            include: {
                skillPreferences: {
                    include: { skillTag: true },
                    orderBy: { createdAt: 'asc' },
                },
            },
        });

        if (!user) {
            throw new NotFoundException('User not found');
        }

        const { passwordHash, deletedAt, ...profile } = user;
        return profile;
    }

    async updateProfile(userId: string, dto: UpdateProfileDto) {
        const user = await this.prisma.user.findFirst({ where: { id: userId, deletedAt: null } });
        if (!user) throw new NotFoundException('User not found');

        const updated = await this.prisma.user.update({
            where: { id: userId },
            data: {
                ...(dto.displayName !== undefined && { displayName: dto.displayName }),
                ...(dto.bio !== undefined && { bio: dto.bio }),
                ...(dto.avatarUrl !== undefined && { avatarUrl: dto.avatarUrl }),
            },
        });

        const { passwordHash, deletedAt, ...profile } = updated;
        return profile;
    }

    // ── Skill Tags ────────────────────────────────────────────────────────────

    async getSkillTags() {
        return this.prisma.skillTag.findMany({
            where: { isGlobal: true },
            orderBy: { name: 'asc' },
        });
    }

    async createSkillTag(name: string) {
        const existing = await this.prisma.skillTag.findUnique({ where: { name } });
        if (existing) throw new BadRequestException(`Skill tag "${name}" already exists`);
        return this.prisma.skillTag.create({ data: { name, isGlobal: true } });
    }

    // ── Skill Preferences ─────────────────────────────────────────────────────

    async addSkillPreference(userId: string, dto: AddSkillPreferenceDto) {
        const skillTag = await this.prisma.skillTag.findUnique({ where: { id: dto.skillTagId } });
        if (!skillTag) throw new NotFoundException('Skill tag not found');

        return this.prisma.userSkillPreference.upsert({
            where: { userId_skillTagId: { userId, skillTagId: dto.skillTagId } },
            create: { userId, skillTagId: dto.skillTagId, level: dto.level },
            update: { level: dto.level },
            include: { skillTag: true },
        });
    }

    async removeSkillPreference(userId: string, skillTagId: string) {
        const preference = await this.prisma.userSkillPreference.findUnique({
            where: { userId_skillTagId: { userId, skillTagId } },
        });

        if (!preference) throw new NotFoundException('Skill preference not found');

        await this.prisma.userSkillPreference.delete({
            where: { userId_skillTagId: { userId, skillTagId } },
        });

        return { message: 'Skill preference removed successfully' };
    }

    // ── Private ───────────────────────────────────────────────────────────────

    private generateAuthResponse(user: any) {
        const payload = { sub: user.id, email: user.email, phoneNumber: user.phoneNumber };
        return {
            access_token: this.jwtService.sign(payload),
            user: {
                id: user.id,
                email: user.email,
                phoneNumber: user.phoneNumber,
                displayName: user.displayName ?? null,
                avatarUrl: user.avatarUrl ?? null,
            },
        };
    }
}
