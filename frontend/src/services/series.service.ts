import { api } from './api';
import type { Series, SeriesWithEpisodes, SeasonInfo } from '../types/series.types';
import type { PaginatedResult } from '../types/channel.types';

export type PaginatedResponse<T> = PaginatedResult<T>;

export interface GetSeriesParams {
    profileId: string;
    page?: number;
    limit?: number;
    search?: string;
}

class SeriesService {
    private basePath = '/profiles';

    async getAllSeries(params: GetSeriesParams): Promise<PaginatedResponse<Series>> {
        const { profileId, ...queryParams } = params;
        const response = await api.get(`${this.basePath}/${profileId}/series`, {
            params: queryParams,
        });
        return response.data;
    }

    async getSeriesById(profileId: string, seriesId: string): Promise<SeriesWithEpisodes> {
        const response = await api.get(`${this.basePath}/${profileId}/series/${seriesId}`);
        return response.data;
    }

    async getSeasons(profileId: string, seriesId: string): Promise<SeasonInfo[]> {
        const response = await api.get(`${this.basePath}/${profileId}/series/${seriesId}/seasons`);
        return response.data.seasons;
    }

    async searchSeries(profileId: string, query: string): Promise<Series[]> {
        const response = await api.get(`${this.basePath}/${profileId}/series/search`, {
            params: { q: query },
        });
        return response.data.series;
    }
}

export const seriesService = new SeriesService();
