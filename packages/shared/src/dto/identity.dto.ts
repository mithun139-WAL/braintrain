export interface LoginDto {
    email: string;
    password?: string;
    provider?: string; // e.g. 'google'
}

export interface RegisterDto {
    email: string;
    password?: string;
    name?: string;
}
