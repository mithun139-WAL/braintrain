import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Twilio } from 'twilio';

@Injectable()
export class SmsService {
    private twilioClient?: Twilio;
    private readonly logger = new Logger(SmsService.name);
    private readonly fromNumber: string;

    constructor(private readonly configService: ConfigService) {
        const accountSid = this.configService.get<string>('TWILIO_ACCOUNT_SID');
        const authToken = this.configService.get<string>('TWILIO_AUTH_TOKEN');
        this.fromNumber = this.configService.get<string>('TWILIO_PHONE_NUMBER') || '';

        if (accountSid && authToken) {
            this.twilioClient = new Twilio(accountSid, authToken);
        } else {
            this.logger.warn('Twilio credentials not fully configured. SMS sending will fail.');
        }
    }

    async sendOtp(toNumber: string, otpCode: string): Promise<void> {
        try {
            if (!this.twilioClient) {
                throw new Error('Twilio client is not initialized');
            }

            await this.twilioClient.messages.create({
                body: `Your BrainTrain verification code is: ${otpCode}. Valid for 1 minute.`,
                from: this.fromNumber,
                to: toNumber,
            });
            this.logger.log(`SMS OTP sent successfully to ${toNumber}`);
        } catch (error) {
            this.logger.error(`Failed to send SMS OTP to ${toNumber}`, error);
            throw error; // Let the caller handle it if necessary
        }
    }
}
