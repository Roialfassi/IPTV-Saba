import { Request, Response, NextFunction } from 'express';
import { SeriesService } from '../services/SeriesService';

export class SeriesController {
    constructor(private seriesService: SeriesService) { }

    getAllSeries = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const { page, limit, search } = req.query;

        const result = await this.seriesService.getAllSeries(profileId, {
            page: page ? Number(page) : 1,
            limit: limit ? Number(limit) : 50,
            search: search as string,
        });

        res.status(200).json(result);
    };

    getSeriesById = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, seriesId } = req.params;
        const series = await this.seriesService.getSeriesById(profileId, seriesId);
        res.status(200).json(series);
    };

    getSeasons = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, seriesId } = req.params;
        const seasons = await this.seriesService.getSeasons(profileId, seriesId);
        res.status(200).json({ seasons });
    };

    searchSeries = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const { q } = req.query;

        const series = await this.seriesService.searchSeries(profileId, q as string);
        res.status(200).json({ series, total: series.length });
    };
}
