import { api } from './api';

export interface Download {
    id: string;
    profileId: string;
    contentType: 'MOVIE' | 'EPISODE';
    contentId: string;
    title: string;
    logo?: string;
    url: string;
    seriesId?: string;
    seriesName?: string;
    seasonNumber?: number;
    episodeNumber?: number;
    status: 'QUEUED' | 'DOWNLOADING' | 'COMPLETED' | 'FAILED' | 'PAUSED';
    progress: number;
    fileSize: number;
    downloadedSize: number;
    filePath?: string;
    error?: string;
    createdAt: string;
    completedAt?: string;
}

export const downloadsService = {
    getDownloads: async (profileId: string): Promise<Download[]> => {
        const response = await api.get(`/profiles/${profileId}/downloads`);
        return response.data;
    },

    queueDownload: async (data: {
        profileId: string;
        contentType: 'MOVIE' | 'EPISODE';
        contentId: string;
        title: string;
        logo?: string;
        url: string;
        seriesId?: string;
        seriesName?: string;
        seasonNumber?: number;
        episodeNumber?: number;
    }): Promise<Download> => {
        const response = await api.post(`/profiles/${data.profileId}/downloads`, data);
        return response.data;
    },

    pauseDownload: async (downloadId: string): Promise<void> => {
        await api.post(`/downloads/${downloadId}/pause`);
    },

    resumeDownload: async (downloadId: string): Promise<void> => {
        await api.post(`/downloads/${downloadId}/resume`);
    },

    deleteDownload: async (downloadId: string): Promise<void> => {
        await api.delete(`/downloads/${downloadId}`);
    },
};
