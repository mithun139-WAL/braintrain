import { IsIn, IsInt, IsOptional, IsPositive, Max } from 'class-validator';
import { Type } from 'class-transformer';

export class ListSessionsDto {
    @IsOptional()
    @IsIn(['CREATED', 'ACTIVE', 'COMPLETED', 'ANALYZED', 'CANCELLED'])
    status?: 'CREATED' | 'ACTIVE' | 'COMPLETED' | 'ANALYZED' | 'CANCELLED';

    @IsOptional()
    @Type(() => Number)
    @IsInt()
    @IsPositive()
    page?: number;

    @IsOptional()
    @Type(() => Number)
    @IsInt()
    @IsPositive()
    @Max(100)
    limit?: number;
}
