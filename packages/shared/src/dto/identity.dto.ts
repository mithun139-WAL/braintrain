export interface LoginDto {
    email?: string;
    phoneNumber?: string;
    password?: string;
    provider?: string; // e.g. 'google'
}

export interface RegisterDto {
    email?: string;
    phoneNumber?: string;
    password?: string;
    name?: string;
}

export interface RequestOtpDto {
    identifier: string; // email or phone number
}

export interface VerifyOtpDto {
    identifier: string;
    code: string;
}

export interface GoogleLoginDto {
    token: string;
}

export interface UpdateProfileDto {
    displayName?: string;
    bio?: string;
    avatarUrl?: string;
}
