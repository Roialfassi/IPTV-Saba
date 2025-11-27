import { api } from './api';
import type { Channel, PaginatedResponse } from '../types/channel.types';

export interface GetChannelsParams {
    profileId: string;
    page?: number;
    limit?: number;
    groupTitle?: string;
    search?: string;
}

export interface StreamInfo {
    available: boolean;
    contentType: string;
    size?: number;
}

class ChannelsService {
    private basePath = '/profiles';

    async getChannels(params: GetChannelsParams): Promise<PaginatedResponse<Channel>> {
        const { profileId, ...queryParams } = params;
        const response = await api.get(`${this.basePath}/${profileId}/channels`, {
            params: queryParams,
        });
        return response.data;
    }

    async getChannelById(profileId: string, channelId: string): Promise<Channel> {
        const response = await api.get(`${this.basePath}/${profileId}/channels/${channelId}`);
        return response.data;
    }

    async getGroupTitles(profileId: string): Promise<string[]> {
        const response = await api.get(`${this.basePath}/${profileId}/channels/groups`);
        return response.data.groups;
    }

    async searchChannels(
        profileId: string,
        query: string,
        groupTitle?: string
    ): Promise<Channel[]> {
        const response = await api.get(`${this.basePath}/${profileId}/channels/search`, {
            params: { q: query, groupTitle },
        });
        return response.data.channels;
    }

    async validateStream(profileId: string, url: string): Promise<StreamInfo> {
        const response = await api.post(`${this.basePath}/${profileId}/channels/stream-info`, {
            url,
        });
        return response.data;
    }
}

export const channelsService = new ChannelsService();
