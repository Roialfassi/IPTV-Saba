import { api } from './api';
import type { Profile, CreateProfileDto, UpdateProfileDto, M3USource, SyncResult } from '../types/profile.types';

class ProfilesService {
    private basePath = '/profiles';

    async getAllProfiles(): Promise<Profile[]> {
        const response = await api.get<{ profiles: Profile[] }>(this.basePath);
        return response.data.profiles;
    }

    async getProfileById(id: string): Promise<Profile> {
        const response = await api.get<Profile>(`${this.basePath}/${id}`);
        return response.data;
    }

    async createProfile(data: CreateProfileDto): Promise<Profile> {
        const response = await api.post<Profile>(this.basePath, data);
        return response.data;
    }

    async updateProfile(id: string, data: UpdateProfileDto): Promise<Profile> {
        const response = await api.patch<Profile>(`${this.basePath}/${id}`, data);
        return response.data;
    }

    async deleteProfile(id: string): Promise<void> {
        await api.delete(`${this.basePath}/${id}`);
    }

    async setActiveProfile(id: string): Promise<Profile> {
        const response = await api.patch<Profile>(`${this.basePath}/${id}/activate`);
        return response.data;
    }

    async addM3USource(profileId: string, url: string, name?: string): Promise<{ source: M3USource; jobId: string }> {
        const response = await api.post(`${this.basePath}/${profileId}/m3u-sources`, {
            url,
            name,
        });
        return response.data;
    }

    async removeM3USource(profileId: string, sourceId: string): Promise<void> {
        await api.delete(`${this.basePath}/${profileId}/m3u-sources/${sourceId}`);
    }

    async syncM3USource(profileId: string, sourceId: string): Promise<{ jobId: string }> {
        const response = await api.post(`${this.basePath}/${profileId}/m3u-sources/${sourceId}/sync`);
        return response.data;
    }

    async getSourceStatus(profileId: string, sourceId: string): Promise<SyncResult> {
        const response = await api.get(`${this.basePath}/${profileId}/m3u-sources/${sourceId}/status`);
        return response.data;
    }
}

export const profilesService = new ProfilesService();
