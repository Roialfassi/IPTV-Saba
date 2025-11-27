import { body, param } from 'express-validator';

export const createProfileValidator = [
    body('name').isString().trim().isLength({ min: 2, max: 50 }),
    body('avatar').optional().isString().trim().isURL(),
];

export const updateProfileValidator = [
    param('profileId').isUUID(),
    body('name').optional().isString().trim().isLength({ min: 2, max: 50 }),
    body('avatar').optional().isString().trim().isURL(),
    body('settings').optional().isObject(),
];

export const profileIdValidator = [
    param('profileId').isUUID(),
];

export const addM3USourceValidator = [
    param('profileId').isUUID(),
    body('url').isURL({ protocols: ['http', 'https'] }),
    body('name').optional().isString().trim(),
];

export const sourceIdValidator = [
    param('profileId').isUUID(),
    param('sourceId').isUUID(),
];
