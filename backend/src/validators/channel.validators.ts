import { param, query, body } from 'express-validator';

export const getChannelsValidator = [
    param('profileId').isUUID(),
    query('page').optional().isInt({ min: 1 }).toInt(),
    query('limit').optional().isInt({ min: 1, max: 100 }).toInt(),
    query('groupTitle').optional().isString().trim(),
    query('search').optional().isString().trim().isLength({ max: 100 }),
];

export const getChannelByIdValidator = [
    param('profileId').isUUID(),
    param('channelId').isUUID(),
];

export const searchChannelsValidator = [
    param('profileId').isUUID(),
    query('q').isString().trim().isLength({ min: 2, max: 100 }),
    query('groupTitle').optional().isString().trim(),
];

export const validateStreamValidator = [
    param('profileId').isUUID(),
    body('url').isURL({ protocols: ['http', 'https'] }),
];

export const getGroupTitlesValidator = [
    param('profileId').isUUID(),
];
