import { Router } from 'express';
import { FavoritesController } from '../controllers/FavoritesController';
import { FavoritesService } from '../services/FavoritesService';
import { repositories } from '../repositories';

const router = Router({ mergeParams: true });

// Initialize dependencies
const favoritesService = new FavoritesService(
    repositories.favorites,
    repositories.channel,
    repositories.series
);
const favoritesController = new FavoritesController(favoritesService);

router.get('/', (req, res, next) => favoritesController.getFavorites(req, res, next));
router.post('/', (req, res, next) => favoritesController.addFavorite(req, res, next));
router.delete('/:contentType/:contentId', (req, res, next) => favoritesController.removeFavorite(req, res, next));
router.get('/check', (req, res, next) => favoritesController.checkFavorite(req, res, next));
router.get('/counts', (req, res, next) => favoritesController.getFavoriteCounts(req, res, next));

export default router;
