import express from 'express';
import { SeriesController } from '../controllers/SeriesController';
import { EpisodeController } from '../controllers/EpisodeController';
import { SeriesService } from '../services/SeriesService';
import { EpisodeService } from '../services/EpisodeService';
import { repositories } from '../repositories';
import {
    getAllSeriesValidator,
    getSeriesByIdValidator,
    getSeasonsValidator,
    searchSeriesValidator,
} from '../validators/series.validators';
import {
    getEpisodesValidator,
    getEpisodesBySeasonValidator,
    getEpisodeValidator,
    getNextEpisodeValidator,
} from '../validators/episode.validators';
import { validate } from '../middleware/validation.middleware';
import { asyncHandler } from '../middleware/errorHandler.middleware';

const router = express.Router();

const episodeService = new EpisodeService(repositories.episode);
const seriesService = new SeriesService(repositories.series, repositories.episode);

const seriesController = new SeriesController(seriesService);
const episodeController = new EpisodeController(episodeService);

// Series Routes
router.get(
    '/profiles/:profileId/series',
    getAllSeriesValidator,
    validate,
    asyncHandler(seriesController.getAllSeries)
);

router.get(
    '/profiles/:profileId/series/search',
    searchSeriesValidator,
    validate,
    asyncHandler(seriesController.searchSeries)
);

router.get(
    '/profiles/:profileId/series/:seriesId',
    getSeriesByIdValidator,
    validate,
    asyncHandler(seriesController.getSeriesById)
);

router.get(
    '/profiles/:profileId/series/:seriesId/seasons',
    getSeasonsValidator,
    validate,
    asyncHandler(seriesController.getSeasons)
);

// Episode Routes (Nested under series)
router.get(
    '/profiles/:profileId/series/:seriesId/episodes',
    getEpisodesValidator,
    validate,
    asyncHandler(episodeController.getEpisodes)
);

router.get(
    '/profiles/:profileId/series/:seriesId/seasons/:season/episodes',
    getEpisodesBySeasonValidator,
    validate,
    asyncHandler(episodeController.getEpisodesBySeason)
);

router.get(
    '/profiles/:profileId/series/:seriesId/seasons/:season/episodes/:episode',
    getEpisodeValidator,
    validate,
    asyncHandler(episodeController.getEpisode)
);

router.get(
    '/profiles/:profileId/series/:seriesId/episodes/next',
    getNextEpisodeValidator,
    validate,
    asyncHandler(episodeController.getNextEpisode)
);

export default router;
