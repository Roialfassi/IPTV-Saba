import { Router } from 'express';
import { WatchHistoryController } from '../controllers/WatchHistoryController';
import { WatchHistoryService } from '../services/WatchHistoryService';
import { repositories } from '../repositories';

const router = Router({ mergeParams: true });

// Initialize dependencies
const historyService = new WatchHistoryService(repositories.history);
const historyController = new WatchHistoryController(historyService);

router.get('/', (req, res, next) => historyController.getHistory(req, res, next));
router.get('/continue-watching', (req, res, next) => historyController.getContinueWatching(req, res, next));
router.post('/progress', (req, res, next) => historyController.updateProgress(req, res, next));
router.get('/progress', (req, res, next) => historyController.getProgress(req, res, next));
router.delete('/:historyId', (req, res, next) => historyController.deleteHistory(req, res, next));
router.delete('/', (req, res, next) => historyController.clearAllHistory(req, res, next));

export default router;
