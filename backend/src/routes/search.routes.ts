import { Router } from 'express';
import { SearchController } from '../controllers/SearchController';
import { SearchService } from '../services/SearchService';
import { db, repositories } from '../repositories';

const router = Router({ mergeParams: true });

// Initialize dependencies
const searchService = new SearchService(db, repositories.channel, repositories.series);
const searchController = new SearchController(searchService);

// Search routes
router.get('/', (req, res, next) => searchController.search(req, res, next));
router.get('/history', (req, res, next) => searchController.getSearchHistory(req, res, next));
router.delete('/history', (req, res, next) => searchController.clearSearchHistory(req, res, next));
router.get('/suggestions', (req, res, next) => searchController.getSuggestions(req, res, next));
router.get('/popular', (req, res, next) => searchController.getPopularSearches(req, res, next));

export default router;
