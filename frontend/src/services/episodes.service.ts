import { api } from './api';
import type { Episode } from '../types/series.types';

class EpisodesService {
    private basePath = '/profiles';

    async getEpisodes(
        profileId: string,
        seriesId: string,
        season?: number
    ): Promise<Episode[]> {
        const response = await api.get(
            `${this.basePath}/${profileId}/series/${seriesId}/episodes`,
            { params: { season } }
        );
        return response.data.episodes;
    }

    async getEpisodesBySeason(
        profileId: string,
        seriesId: string,
        seasonNumber: number
    ): Promise<Episode[]> {
        const response = await api.get(
            `${this.basePath}/${profileId}/series/${seriesId}/seasons/${seasonNumber}/episodes`
        );
        return response.data.episodes;
    }

    async getEpisode(
        profileId: string,
        seriesId: string,
        seasonNumber: number,
        episodeNumber: number
    ): Promise<Episode> {
        const response = await api.get(
            `${this.basePath}/${profileId}/series/${seriesId}/seasons/${seasonNumber}/episodes/${episodeNumber}`
        );
        return response.data;
    }

    async getNextEpisode(
        profileId: string,
        seriesId: string,
        currentSeason: number,
        currentEpisode: number
    ): Promise<Episode | null> {
        try {
            const response = await api.get(
                `${this.basePath}/${profileId}/series/${seriesId}/episodes/next`,
                { params: { currentSeason, currentEpisode } }
            );
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                return null; // No next episode
            }
            throw error;
        }
    }
}

export const episodesService = new EpisodesService();
