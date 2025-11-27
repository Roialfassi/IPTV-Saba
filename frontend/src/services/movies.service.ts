import { api } from './api';
import type { Movie } from '../types/movie.types';
import type { PaginatedResult } from '../types/channel.types';

export type PaginatedResponse<T> = PaginatedResult<T>;

export interface GetMoviesParams {
    profileId: string;
    page?: number;
    limit?: number;
    groupTitle?: string;
    year?: number;
    sortBy?: 'name' | 'year' | 'date';
    order?: 'asc' | 'desc';
    search?: string;
}

class MoviesService {
    private basePath = '/profiles';

    async getMovies(params: GetMoviesParams): Promise<PaginatedResponse<Movie>> {
        const { profileId, ...queryParams } = params;
        const response = await api.get(`${this.basePath}/${profileId}/movies`, {
            params: queryParams,
        });
        return response.data;
    }

    async getMovieById(profileId: string, movieId: string): Promise<Movie> {
        const response = await api.get(`${this.basePath}/${profileId}/movies/${movieId}`);
        return response.data;
    }

    async getMovieGroups(profileId: string): Promise<string[]> {
        const response = await api.get(`${this.basePath}/${profileId}/movies/groups`);
        return response.data.groups;
    }

    async getAvailableYears(profileId: string): Promise<number[]> {
        const response = await api.get(`${this.basePath}/${profileId}/movies/years`);
        return response.data.years;
    }

    async searchMovies(
        profileId: string,
        query: string,
        filters?: { year?: number; groupTitle?: string }
    ): Promise<Movie[]> {
        const response = await api.get(`${this.basePath}/${profileId}/movies/search`, {
            params: { q: query, ...filters },
        });
        return response.data.movies;
    }
}

export const moviesService = new MoviesService();
