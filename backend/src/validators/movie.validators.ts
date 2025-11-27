import { param, query } from 'express-validator';

export const getMoviesValidator = [
    param('profileId').isUUID(),
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 100 }).toInt(),
    query('groupTitle').optional().isString().trim(),
    query('year').optional().isInt({ min: 1900, max: 2100 }).toInt(),
    query('sortBy').optional().isIn(['name', 'year', 'date']),
    query('order').optional().isIn(['asc', 'desc']),
];

export const getMovieByIdValidator = [
    param('profileId').isUUID(),
    param('movieId').isUUID(),
];

export const searchMoviesValidator = [
    param('profileId').isUUID(),
    query('q').isString().trim().isLength({ min: 2, max: 100 }),
    query('year').optional().isInt({ min: 1900, max: 2100 }).toInt(),
    query('groupTitle').optional().isString().trim(),
];

export const getYearsValidator = [
    param('profileId').isUUID(),
];
