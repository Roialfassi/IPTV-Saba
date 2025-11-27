import { Request, Response, NextFunction } from 'express';
import { SearchService } from '../services/SearchService';

export class SearchController {
    constructor(private searchService: SearchService) { }

    // GET /api/v1/profiles/:profileId/search
    async search(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { q, contentTypes, groupTitles, years, limit } = req.query;

            if (!q || typeof q !== 'string') {
                return res.status(400).json({ error: 'Query parameter is required' });
            }

            const filters = {
                contentTypes: contentTypes
                    ? (contentTypes as string).split(',')
                    : undefined,
                groupTitles: groupTitles
                    ? (groupTitles as string).split(',')
                    : undefined,
                years: years
                    ? (years as string).split(',').map(Number)
                    : undefined,
            };

            const results = await this.searchService.globalSearch(
                profileId,
                q,
                filters as any,
                limit ? parseInt(limit as string) : 20
            );

            res.json(results);
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/profiles/:profileId/search/history
    async getSearchHistory(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { limit } = req.query;

            const history = await this.searchService.getSearchHistory(
                profileId,
                limit ? parseInt(limit as string) : 10
            );

            res.json({ history });
        } catch (error) {
            next(error);
        }
    }

    // DELETE /api/v1/profiles/:profileId/search/history
    async clearSearchHistory(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            await this.searchService.clearSearchHistory(profileId);
            res.json({ success: true });
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/profiles/:profileId/search/suggestions
    async getSuggestions(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { q } = req.query;

            if (!q || typeof q !== 'string') {
                return res.json({ suggestions: [] });
            }

            const suggestions = await this.searchService.getSuggestions(profileId, q);
            res.json({ suggestions });
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/profiles/:profileId/search/popular
    async getPopularSearches(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const { limit } = req.query;

            const popular = await this.searchService.getPopularSearches(
                profileId,
                limit ? parseInt(limit as string) : 10
            );

            res.json({ popular });
        } catch (error) {
            next(error);
        }
    }
}
