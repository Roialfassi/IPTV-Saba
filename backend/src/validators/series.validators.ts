import { param, query } from 'express-validator';

export const getAllSeriesValidator = [
    param('profileId').isUUID(),
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 100 }).toInt(),
    query('search').optional().isString().trim().isLength({ max: 100 }),
];

export const getSeriesByIdValidator = [
    param('profileId').isUUID(),
    param('seriesId').isUUID(),
];

export const getSeasonsValidator = [
    param('profileId').isUUID(),
    param('seriesId').isUUID(),
];

export const searchSeriesValidator = [
    param('profileId').isUUID(),
    query('q').isString().trim().isLength({ min: 2, max: 100 }),
];
