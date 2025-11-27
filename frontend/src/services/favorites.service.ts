import { api } from './api';

export interface Favorite {
    id: string;
    profileId: string;
    contentType: 'CHANNEL' | 'MOVIE' | 'SERIES';
    contentId: string;
    title: string;
    logo?: string;
    url?: string;
    createdAt: string;
}

export interface FavoritesResponse {
    favorites: Favorite[];
    total: number;
    page: number;
    totalPages: number;
}

export const favoritesService = {
    getFavorites: async (
        profileId: string,
        contentType?: string,
        page: number = 1,
        limit: number = 20
    ): Promise<FavoritesResponse> => {
        const response = await api.get(`/profiles/${profileId}/favorites`, {
            params: { contentType, page, limit },
        });
        return response.data;
    },

    addFavorite: async (
        profileId: string,
        contentType: 'CHANNEL' | 'MOVIE' | 'SERIES',
        contentId: string
    ): Promise<Favorite> => {
        const response = await api.post(`/profiles/${profileId}/favorites`, {
            contentType,
            contentId,
        });
        return response.data;
    },

    removeFavorite: async (
        profileId: string,
        contentType: string,
        contentId: string
    ): Promise<void> => {
        await api.delete(`/profiles/${profileId}/favorites/${contentType}/${contentId}`);
    },

    checkFavorite: async (
        profileId: string,
        contentType: string,
        contentId: string
    ): Promise<boolean> => {
        const response = await api.get(`/profiles/${profileId}/favorites/check`, {
            params: { contentType, contentId },
        });
        return response.data.isFavorite;
    },

    getCounts: async (profileId: string) => {
        const response = await api.get(`/profiles/${profileId}/favorites/counts`);
        return response.data;
    },
};
