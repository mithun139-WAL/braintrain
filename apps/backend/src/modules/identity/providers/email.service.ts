import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import * as nodemailer from 'nodemailer';

@Injectable()
export class EmailService {
    private transporter: nodemailer.Transporter;
    private readonly logger = new Logger(EmailService.name);

    constructor(private readonly configService: ConfigService) {
        const port = this.configService.get<string>('SMTP_PORT');
        const portNumber = port ? parseInt(port, 10) : 587;

        this.transporter = nodemailer.createTransport({
            host: this.configService.get<string>('SMTP_HOST'),
            port: portNumber,
            secure: portNumber === 465, // true for 465, false for 587
            auth: {
                user: this.configService.get<string>('SMTP_USER'),
                pass: this.configService.get<string>('SMTP_PASS'),
            },
        });
    }

    async sendOtp(toEmail: string, otpCode: string): Promise<void> {
        const fromEmail = this.configService.get<string>('SMTP_FROM', 'noreply@braintrain.ai');

        const mailOptions = {
            from: `"BrainTrain Support" <${fromEmail}>`,
            to: toEmail,
            subject: 'Your BrainTrain Verification Code',
            text: `Your BrainTrain verification code is: ${otpCode}\n\nThis code will expire in 2 minutes.`,
            html: `
                <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                    <h2>BrainTrain Verification</h2>
                    <p>Your verification code is:</p>
                    <h1 style="font-size: 32px; letter-spacing: 4px; color: #007bff;">${otpCode}</h1>
                    <p>This code will expire in 2 minutes. Please do not share this code with anyone.</p>
                </div>
            `,
        };

        try {
            await this.transporter.sendMail(mailOptions);
            this.logger.log(`Email OTP sent successfully to ${toEmail}`);
        } catch (error) {
            this.logger.error(`Failed to send email OTP to ${toEmail}`, error);
            throw error; // Let the caller handle it if necessary
        }
    }
}
