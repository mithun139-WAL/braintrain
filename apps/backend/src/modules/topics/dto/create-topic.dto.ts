import { IsNotEmpty, IsOptional, IsString, MaxLength } from 'class-validator';

export class CreateTopicDto {
    @IsString()
    @IsNotEmpty()
    @MaxLength(150)
    name!: string;

    @IsOptional()
    @IsString()
    @IsNotEmpty()
    parentTopicId?: string;
}
