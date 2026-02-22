import {
    ExceptionFilter,
    Catch,
    ArgumentsHost,
    HttpException,
    HttpStatus,
    Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

/**
 * GlobalExceptionFilter — consistent error response shape for all unhandled exceptions.
 *
 * Every error the API returns will have this structure:
 * {
 *   code:    string;   e.g. "NOT_FOUND", "FORBIDDEN", "INTERNAL_ERROR"
 *   message: string;   human-readable message
 *   details?: unknown; optional extra context
 * }
 *
 * Register globally in main.ts:
 *   app.useGlobalFilters(new GlobalExceptionFilter());
 */
@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
    private readonly logger = new Logger(GlobalExceptionFilter.name);

    catch(exception: unknown, host: ArgumentsHost) {
        const ctx = host.switchToHttp();
        const response = ctx.getResponse<Response>();
        const request = ctx.getRequest<Request>();

        let status = HttpStatus.INTERNAL_SERVER_ERROR;
        let code = 'INTERNAL_ERROR';
        let message = 'An unexpected error occurred';
        let details: unknown;

        if (exception instanceof HttpException) {
            status = exception.getStatus();
            const exceptionResponse = exception.getResponse();

            // Map HTTP status codes to readable error codes
            code = this.statusToCode(status);
            message =
                typeof exceptionResponse === 'string'
                    ? exceptionResponse
                    : (exceptionResponse as any).message ?? message;
            details =
                typeof exceptionResponse === 'object' &&
                    (exceptionResponse as any).details
                    ? (exceptionResponse as any).details
                    : undefined;
        } else if (exception instanceof Error) {
            this.logger.error(
                `Unhandled exception on ${request.method} ${request.url}: ${exception.message}`,
                exception.stack,
            );
        }

        // Don't log 4xx client errors as errors — only 5xx server errors
        if (status >= 500) {
            this.logger.error(
                `${request.method} ${request.url} → ${status} ${code}: ${message}`,
            );
        } else {
            this.logger.warn(
                `${request.method} ${request.url} → ${status} ${code}: ${message}`,
            );
        }

        const errorBody: Record<string, unknown> = { code, message };
        if (details !== undefined) errorBody.details = details;

        response.status(status).json(errorBody);
    }

    private statusToCode(status: number): string {
        const map: Record<number, string> = {
            400: 'BAD_REQUEST',
            401: 'UNAUTHORIZED',
            403: 'FORBIDDEN',
            404: 'NOT_FOUND',
            409: 'CONFLICT',
            422: 'UNPROCESSABLE',
            429: 'TOO_MANY_REQUESTS',
            500: 'INTERNAL_ERROR',
            502: 'BAD_GATEWAY',
            503: 'SERVICE_UNAVAILABLE',
        };
        return map[status] ?? 'ERROR';
    }
}
