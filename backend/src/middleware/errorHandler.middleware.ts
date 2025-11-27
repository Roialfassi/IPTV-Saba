import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';
import { ZodError } from 'zod';

export class AppError extends Error {
    constructor(
        public statusCode: number,
        public message: string,
        public isOperational = true
    ) {
        super(message);
        Object.setPrototypeOf(this, AppError.prototype);
    }
}

export const errorHandler = (
    err: Error,
    req: Request,
    res: Response,
    next: NextFunction
) => {
    if (err instanceof AppError) {
        if (err.statusCode >= 500) {
            logger.error(`AppError: ${err.message}`);
        } else {
            logger.warn(`AppError: ${err.message}`);
        }
        return res.status(err.statusCode).json({
            status: 'error',
            message: err.message,
        });
    }

    if (err instanceof ZodError) {
        return res.status(400).json({
            status: 'error',
            message: 'Validation Error',
            errors: err.errors,
        });
    }

    // Prisma Errors (simplified)
    if ((err as any).code && (err as any).code.startsWith('P')) {
        logger.error(`Prisma Error: ${err.message}`);
        return res.status(400).json({
            status: 'error',
            message: 'Database operation failed',
            code: (err as any).code
        });
    }

    logger.error(`Unhandled Error: ${err.stack}`);
    res.status(500).json({
        status: 'error',
        message: 'Internal Server Error',
    });
};

export const asyncHandler = (fn: Function) => (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};
