import { api } from './api';

export interface SearchFilters {
    contentTypes?: ('CHANNEL' | 'MOVIE' | 'SERIES')[];
    groupTitles?: string[];
    years?: number[];
    minDuration?: number;
    maxDuration?: number;
}

export interface SearchResult {
    channels: any[];
    movies: any[];
    series: any[];
    total: number;
}

export interface SearchHistoryItem {
    id: string;
    query: string;
    filters: any;
    resultCount: number;
    createdAt: string;
}

export const searchService = {
    search: async (
        profileId: string,
        query: string,
        filters?: SearchFilters,
        limit: number = 20
    ): Promise<SearchResult> => {
        const params: any = { q: query, limit };
        if (filters) {
            if (filters.contentTypes) params.contentTypes = filters.contentTypes.join(',');
            if (filters.groupTitles) params.groupTitles = filters.groupTitles.join(',');
            if (filters.years) params.years = filters.years.join(',');
        }
        const response = await api.get(`/profiles/${profileId}/search`, { params });
        return response.data;
    },

    getHistory: async (profileId: string, limit: number = 10): Promise<SearchHistoryItem[]> => {
        const response = await api.get(`/profiles/${profileId}/search/history`, {
            params: { limit },
        });
        return response.data.history;
    },

    clearHistory: async (profileId: string): Promise<void> => {
        await api.delete(`/profiles/${profileId}/search/history`);
    },

    getSuggestions: async (profileId: string, query: string): Promise<string[]> => {
        const response = await api.get(`/profiles/${profileId}/search/suggestions`, {
            params: { q: query },
        });
        return response.data.suggestions;
    },

    getPopular: async (profileId: string, limit: number = 10): Promise<{ query: string; count: number }[]> => {
        const response = await api.get(`/profiles/${profileId}/search/popular`, {
            params: { limit },
        });
        return response.data.popular;
    },
};
