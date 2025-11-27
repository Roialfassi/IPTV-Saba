import { api } from './api';
import type { WatchHistory, UpdateProgressData } from '../types/history.types';

export const historyService = {
    getHistory: async (
        profileId: string,
        page: number = 1,
        limit: number = 20
    ) => {
        const response = await api.get(`/profiles/${profileId}/history`, {
            params: { page, limit },
        });
        return response.data;
    },

    getContinueWatching: async (
        profileId: string,
        limit: number = 10
    ): Promise<WatchHistory[]> => {
        const response = await api.get(`/profiles/${profileId}/history/continue-watching`, {
            params: { limit },
        });
        return response.data.items;
    },

    updateProgress: async (
        profileId: string,
        data: UpdateProgressData
    ): Promise<WatchHistory | null> => {
        const response = await api.post(`/profiles/${profileId}/history/progress`, data);
        return response.data;
    },

    getProgress: async (
        profileId: string,
        contentType: string,
        contentId: string
    ) => {
        const response = await api.get(`/profiles/${profileId}/history/progress`, {
            params: { contentType, contentId },
        });
        return response.data;
    },

    deleteHistory: async (profileId: string, historyId: string) => {
        await api.delete(`/profiles/${profileId}/history/${historyId}`);
    },

    clearAllHistory: async (profileId: string) => {
        await api.delete(`/profiles/${profileId}/history`);
    },
};
