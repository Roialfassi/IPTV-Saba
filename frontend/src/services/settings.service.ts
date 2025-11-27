import { api } from './api';

export interface ProfileSettings {
    id: string;
    profileId: string;

    // Playback settings
    autoplay: boolean;
    defaultQuality: string;
    skipIntroSeconds: number;
    defaultVolume: number;
    subtitlesEnabled: boolean;
    subtitlesLanguage: string;

    // Appearance settings
    theme: string;
    accentColor: string;
    compactMode: boolean;
    showEPG: boolean;
    gridSize: string;

    // Content settings
    contentLanguage: string;
    ageRating: string;
    hideAdultContent: boolean;

    // Data settings
    cacheEnabled: boolean;
    cacheSize: number;
    downloadQuality: string;
    wifiOnlyDownloads: boolean;

    // Notifications
    reminderEnabled: boolean;
    reminderMinutes: number;
    newContentAlert: boolean;

    createdAt: string;
    updatedAt: string;
}

export interface UpdateSettingsData extends Partial<Omit<ProfileSettings, 'id' | 'profileId' | 'createdAt' | 'updatedAt'>> { }

export const settingsService = {
    getSettings: async (profileId: string): Promise<ProfileSettings> => {
        const response = await api.get(`/profiles/${profileId}/settings`);
        return response.data;
    },

    updateSettings: async (profileId: string, data: UpdateSettingsData): Promise<ProfileSettings> => {
        const response = await api.patch(`/profiles/${profileId}/settings`, data);
        return response.data;
    },

    resetSettings: async (profileId: string): Promise<ProfileSettings> => {
        const response = await api.post(`/profiles/${profileId}/settings/reset`);
        return response.data;
    },

    exportSettings: async (profileId: string): Promise<any> => {
        const response = await api.get(`/profiles/${profileId}/settings/export`);
        return response.data;
    },

    importSettings: async (profileId: string, data: any): Promise<ProfileSettings> => {
        const response = await api.post(`/profiles/${profileId}/settings/import`, data);
        return response.data;
    },
};
