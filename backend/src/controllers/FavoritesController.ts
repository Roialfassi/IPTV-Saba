import { Request, Response, NextFunction } from 'express';
import { FavoritesService } from '../services/FavoritesService';

export class FavoritesController {
    constructor(private favoritesService: FavoritesService) { }

    // GET /api/v1/profiles/:profileId/favorites
    async getFavorites(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { contentType, page, limit } = req.query;

            const result = await this.favoritesService.getFavorites(
                profileId,
                contentType as string | undefined,
                page ? parseInt(page as string) : 1,
                limit ? parseInt(limit as string) : 20
            );

            res.json(result);
        } catch (error) {
            next(error);
        }
    }

    // POST /api/v1/profiles/:profileId/favorites
    async addFavorite(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { contentType, contentId } = req.body;

            const favorite = await this.favoritesService.addFavorite(
                profileId,
                contentType,
                contentId
            );

            res.status(201).json(favorite);
        } catch (error) {
            next(error);
        }
    }

    // DELETE /api/v1/profiles/:profileId/favorites/:contentType/:contentId
    async removeFavorite(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId, contentType, contentId } = req.params;

            await this.favoritesService.removeFavorite(
                profileId,
                contentType,
                contentId
            );

            res.json({ success: true });
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/profiles/:profileId/favorites/check
    async checkFavorite(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { contentType, contentId } = req.query;

            const isFavorite = await this.favoritesService.isFavorite(
                profileId,
                contentType as string,
                contentId as string
            );

            res.json({ isFavorite });
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/profiles/:profileId/favorites/counts
    async getFavoriteCounts(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const counts = await this.favoritesService.getFavoriteCounts(profileId);
            res.json(counts);
        } catch (error) {
            next(error);
        }
    }
}
