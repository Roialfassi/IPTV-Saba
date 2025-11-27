import { Request, Response, NextFunction } from 'express';
import { SettingsService } from '../services/SettingsService';

export class SettingsController {
    constructor(private settingsService: SettingsService) { }

    // GET /api/v1/profiles/:profileId/settings
    async getSettings(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const settings = await this.settingsService.getSettings(profileId);
            res.json(settings);
        } catch (error) {
            next(error);
        }
    }

    // PATCH /api/v1/profiles/:profileId/settings
    async updateSettings(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const data = req.body;
            const settings = await this.settingsService.updateSettings(profileId, data);
            res.json(settings);
        } catch (error) {
            next(error);
        }
    }

    // POST /api/v1/profiles/:profileId/settings/reset
    async resetSettings(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const settings = await this.settingsService.resetSettings(profileId);
            res.json(settings);
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/profiles/:profileId/settings/export
    async exportSettings(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const exportData = await this.settingsService.exportSettings(profileId);
            res.json(exportData);
        } catch (error) {
            next(error);
        }
    }

    // POST /api/v1/profiles/:profileId/settings/import
    async importSettings(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const data = req.body;
            const settings = await this.settingsService.importSettings(profileId, data);
            res.json(settings);
        } catch (error) {
            next(error);
        }
    }
}
