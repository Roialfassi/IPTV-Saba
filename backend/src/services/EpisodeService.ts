import { EpisodeRepository } from '../repositories/EpisodeRepository';
import { Episode } from '@prisma/client';
import { AppError } from '../middleware/errorHandler.middleware';

export interface EpisodeWithSeriesInfo extends Episode {
    seriesName?: string; // Optional as we might not always fetch it or it might be in relation
}

export class EpisodeService {
    constructor(private episodeRepo: EpisodeRepository) { }

    async getEpisodes(
        profileId: string,
        seriesId: string,
        season?: number
    ): Promise<Episode[]> {
        // Ideally we should verify series belongs to profile here, but for performance we might skip if trusted
        // or do a quick check. Assuming seriesId is valid for now or handled by caller/middleware.

        if (season) {
            return this.episodeRepo.findBySeason(seriesId, season);
        }
        return this.episodeRepo.findBySeriesId(seriesId);
    }

    async getEpisodesBySeason(
        profileId: string,
        seriesId: string,
        seasonNumber: number
    ): Promise<Episode[]> {
        return this.episodeRepo.findBySeason(seriesId, seasonNumber);
    }

    async getEpisode(
        profileId: string,
        seriesId: string,
        seasonNumber: number,
        episodeNumber: number
    ): Promise<EpisodeWithSeriesInfo> {
        const episode = await this.episodeRepo.findEpisode(seriesId, seasonNumber, episodeNumber);

        if (!episode) {
            throw new AppError(404, 'Episode not found');
        }

        // To get series info we would need to fetch it or include it in repo query
        // For now returning episode as is, assuming frontend has series context or we add include in repo
        return episode;
    }

    async getNextEpisode(
        profileId: string,
        seriesId: string,
        currentSeason: number,
        currentEpisode: number
    ): Promise<Episode | null> {
        // Try next episode in same season
        let nextEpisode = await this.episodeRepo.findEpisode(seriesId, currentSeason, currentEpisode + 1);

        if (nextEpisode) {
            return nextEpisode;
        }

        // Try first episode of next season
        // We need to find what the next season is (it might not be currentSeason + 1 if there are gaps)
        // But typically it is +1. Let's try +1 first.
        nextEpisode = await this.episodeRepo.findEpisode(seriesId, currentSeason + 1, 1);

        if (nextEpisode) {
            return nextEpisode;
        }

        // If we want to be robust about gaps, we should get all season numbers and find next
        const seasons = await this.episodeRepo.getSeasonNumbers(seriesId);
        const nextSeason = seasons.find(s => s > currentSeason);

        if (nextSeason) {
            return this.episodeRepo.findEpisode(seriesId, nextSeason, 1);
        }

        return null;
    }
}
