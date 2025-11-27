import express from 'express';
import { MovieController } from '../controllers/MovieController';
import { MovieService } from '../services/MovieService';
import { repositories } from '../repositories';
import {
    getMoviesValidator,
    getMovieByIdValidator,
    searchMoviesValidator,
    getYearsValidator,
} from '../validators/movie.validators';
import { validate } from '../middleware/validation.middleware';
import { asyncHandler } from '../middleware/errorHandler.middleware';
import { param } from 'express-validator';

const router = express.Router();
const movieService = new MovieService(repositories.channel);
const movieController = new MovieController(movieService);

router.get(
    '/profiles/:profileId/movies',
    getMoviesValidator,
    validate,
    asyncHandler(movieController.getMovies)
);

router.get(
    '/profiles/:profileId/movies/groups',
    [param('profileId').isUUID()],
    validate,
    asyncHandler(movieController.getMovieGroups)
);

router.get(
    '/profiles/:profileId/movies/years',
    getYearsValidator,
    validate,
    asyncHandler(movieController.getAvailableYears)
);

router.get(
    '/profiles/:profileId/movies/search',
    searchMoviesValidator,
    validate,
    asyncHandler(movieController.searchMovies)
);

router.get(
    '/profiles/:profileId/movies/:movieId',
    getMovieByIdValidator,
    validate,
    asyncHandler(movieController.getMovieById)
);

export default router;
