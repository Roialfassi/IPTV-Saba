import { Request, Response, NextFunction } from 'express';
import { EpisodeService } from '../services/EpisodeService';

export class EpisodeController {
    constructor(private episodeService: EpisodeService) { }

    getEpisodes = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, seriesId } = req.params;
        const { season } = req.query;

        const episodes = await this.episodeService.getEpisodes(
            profileId,
            seriesId,
            season ? Number(season) : undefined
        );

        res.status(200).json({ episodes });
    };

    getEpisodesBySeason = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, seriesId, season } = req.params;

        const episodes = await this.episodeService.getEpisodesBySeason(
            profileId,
            seriesId,
            Number(season)
        );

        res.status(200).json({ season: Number(season), episodes });
    };

    getEpisode = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, seriesId, season, episode } = req.params;

        const result = await this.episodeService.getEpisode(
            profileId,
            seriesId,
            Number(season),
            Number(episode)
        );

        res.status(200).json(result);
    };

    getNextEpisode = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, seriesId } = req.params;
        const { currentSeason, currentEpisode } = req.query;

        const nextEp = await this.episodeService.getNextEpisode(
            profileId,
            seriesId,
            Number(currentSeason),
            Number(currentEpisode)
        );

        if (!nextEp) {
            return res.status(404).json({ message: 'No next episode found' });
        }

        res.status(200).json(nextEp);
    };
}
