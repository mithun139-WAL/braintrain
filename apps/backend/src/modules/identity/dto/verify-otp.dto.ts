import { IsNotEmpty, IsString } from 'class-validator';

export class VerifyOtpDto {
    @IsNotEmpty()
    @IsString()
    identifier!: string; // email or phone number

    @IsNotEmpty()
    @IsString()
    code!: string;
}
