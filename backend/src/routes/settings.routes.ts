import { Router } from 'express';
import { SettingsController } from '../controllers/SettingsController';
import { SettingsService } from '../services/SettingsService';
import { db } from '../repositories';

const router = Router({ mergeParams: true });

// Initialize dependencies
const settingsService = new SettingsService(db);
const settingsController = new SettingsController(settingsService);

// Settings routes
router.get('/', (req, res, next) => settingsController.getSettings(req, res, next));
router.patch('/', (req, res, next) => settingsController.updateSettings(req, res, next));
router.post('/reset', (req, res, next) => settingsController.resetSettings(req, res, next));
router.get('/export', (req, res, next) => settingsController.exportSettings(req, res, next));
router.post('/import', (req, res, next) => settingsController.importSettings(req, res, next));

export default router;
