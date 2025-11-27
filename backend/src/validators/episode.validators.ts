import { param, query } from 'express-validator';

export const getEpisodesValidator = [
    param('profileId').isUUID(),
    param('seriesId').isUUID(),
    query('season').optional().isInt({ min: 1 }).toInt(),
];

export const getEpisodesBySeasonValidator = [
    param('profileId').isUUID(),
    param('seriesId').isUUID(),
    param('season').isInt({ min: 1 }).toInt(),
];

export const getEpisodeValidator = [
    param('profileId').isUUID(),
    param('seriesId').isUUID(),
    param('season').isInt({ min: 1 }).toInt(),
    param('episode').isInt({ min: 1 }).toInt(),
];

export const getNextEpisodeValidator = [
    param('profileId').isUUID(),
    param('seriesId').isUUID(),
    query('currentSeason').isInt({ min: 1 }).toInt(),
    query('currentEpisode').isInt({ min: 1 }).toInt(),
];
