import { Router } from 'express';
import { DownloadController } from '../controllers/DownloadController';
import { DownloadService } from '../services/DownloadService';
import { db } from '../repositories';

const router = Router({ mergeParams: true });

// Initialize dependencies
// Note: DownloadService takes PrismaClient directly, not a repository
const downloadService = new DownloadService(db);
const downloadController = new DownloadController(downloadService);

// Profile-scoped routes
router.get('/profiles/:profileId/downloads', (req, res, next) => downloadController.getDownloads(req, res, next));
router.post('/profiles/:profileId/downloads', (req, res, next) => downloadController.queueDownload(req, res, next));

// Download-specific routes
router.post('/downloads/:downloadId/pause', (req, res, next) => downloadController.pauseDownload(req, res, next));
router.post('/downloads/:downloadId/resume', (req, res, next) => downloadController.resumeDownload(req, res, next));
router.delete('/downloads/:downloadId', (req, res, next) => downloadController.deleteDownload(req, res, next));
router.get('/downloads/:downloadId/stream', (req, res, next) => downloadController.streamDownload(req, res, next));

export default router;
