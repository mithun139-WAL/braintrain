import {
    Injectable,
    NestInterceptor,
    ExecutionContext,
    CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface ApiResponse<T> {
    success: boolean;
    data: T;
    message?: string;
}

@Injectable()
export class ResponseInterceptor<T> implements NestInterceptor<T, ApiResponse<T>> {
    intercept(
        context: ExecutionContext,
        next: CallHandler,
    ): Observable<ApiResponse<T>> {
        return next.handle().pipe(
            map((data) => {
                // If it's already an ApiResponse structure, return as is
                if (data && typeof data === 'object' && 'success' in data) {
                    return data;
                }

                // Standardize the response
                return {
                    success: true,
                    data: data,
                    message: data?.message || undefined,
                };
            }),
        );
    }
}
