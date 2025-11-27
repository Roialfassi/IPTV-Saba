import { Request, Response, NextFunction } from 'express';
import { WatchHistoryService } from '../services/WatchHistoryService';

export class WatchHistoryController {
    constructor(private historyService: WatchHistoryService) { }

    // GET /api/v1/profiles/:profileId/history
    async getHistory(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { page, limit } = req.query;

            const result = await this.historyService.getHistory(
                profileId,
                page ? parseInt(page as string) : 1,
                limit ? parseInt(limit as string) : 20
            );

            res.json(result);
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/profiles/:profileId/history/continue-watching
    async getContinueWatching(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { limit } = req.query;

            const items = await this.historyService.getContinueWatching(
                profileId,
                limit ? parseInt(limit as string) : 10
            );

            res.json({ items });
        } catch (error) {
            next(error);
        }
    }

    // POST /api/v1/profiles/:profileId/history/progress
    async updateProgress(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const data = req.body;

            const history = await this.historyService.updateProgress({
                profileId,
                ...data,
            });

            res.json(history);
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/profiles/:profileId/history/progress
    async getProgress(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { contentType, contentId } = req.query;

            const progress = await this.historyService.getProgress(
                profileId,
                contentType as string,
                contentId as string
            );

            res.json(progress);
        } catch (error) {
            next(error);
        }
    }

    // DELETE /api/v1/profiles/:profileId/history/:historyId
    async deleteHistory(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId, historyId } = req.params;
            await this.historyService.deleteHistory(profileId, historyId);
            res.json({ success: true });
        } catch (error) {
            next(error);
        }
    }

    // DELETE /api/v1/profiles/:profileId/history
    async clearAllHistory(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const count = await this.historyService.clearAllHistory(profileId);
            res.json({ success: true, deletedCount: count });
        } catch (error) {
            next(error);
        }
    }
}
