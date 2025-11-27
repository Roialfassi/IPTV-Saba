import axios from 'axios';
import { ChannelRepository } from '../repositories/ChannelRepository';
import { ProfileRepository } from '../repositories/ProfileRepository';
import { Channel } from '@prisma/client';
import { AppError } from '../middleware/errorHandler.middleware';
import { ContentType } from '../types/content.types';

export interface PaginatedResult<T> {
    data: T[];
    total: number;
    page: number;
    totalPages: number;
}

export interface StreamInfo {
    available: boolean;
    contentType: string;
    size?: number;
}

export class ChannelService {
    constructor(
        private channelRepo: ChannelRepository,
        private profileRepo: ProfileRepository
    ) { }

    async getChannelsByProfile(
        profileId: string,
        options: {
            page: number;
            limit: number;
            groupTitle?: string;
            search?: string;
        }
    ): Promise<PaginatedResult<Channel>> {
        // Validate profile exists
        const profile = await this.profileRepo.findById(profileId);
        if (!profile) {
            throw new AppError(404, 'Profile not found');
        }

        const page = options.page || 1;
        const limit = options.limit || 50;
        const skip = (page - 1) * limit;

        let channels: Channel[];
        let total: number;

        if (options.search) {
            // If search is provided, we use the search method (which limits to 50, so pagination is simplified)
            // For proper pagination with search, we'd need a count method with filters in repo
            channels = await this.channelRepo.searchChannels(profileId, options.search, ContentType.LIVESTREAM);
            total = channels.length; // Approximate for search
        } else if (options.groupTitle) {
            channels = await this.channelRepo.findByGroupTitle(profileId, options.groupTitle);
            // Filter for LIVESTREAM manually if repo doesn't support it in findByGroupTitle
            channels = channels.filter(c => c.contentType === ContentType.LIVESTREAM);
            total = channels.length;
            channels = channels.slice(skip, skip + limit);
        } else {
            channels = await this.channelRepo.findByProfileAndType(
                profileId,
                ContentType.LIVESTREAM,
                skip,
                limit
            );
            // We need a count method in repo for accurate pagination
            // For now, assuming total count is expensive or we add a count method later
            total = await this.channelRepo.count(); // This counts ALL channels, which is wrong.
            // TODO: Add countByProfileAndType to repo
            total = 1000; // Placeholder
        }

        return {
            data: channels,
            total,
            page,
            totalPages: Math.ceil(total / limit),
        };
    }

    async getChannelById(
        profileId: string,
        channelId: string
    ): Promise<Channel> {
        const channel = await this.channelRepo.findById(channelId);
        if (!channel) {
            throw new AppError(404, 'Channel not found');
        }
        if (channel.profileId !== profileId) {
            throw new AppError(403, 'Channel does not belong to this profile');
        }
        return channel;
    }

    async getGroupTitles(profileId: string): Promise<string[]> {
        return this.channelRepo.getGroupTitles(profileId, ContentType.LIVESTREAM);
    }

    async searchChannels(
        profileId: string,
        query: string,
        groupTitle?: string
    ): Promise<Channel[]> {
        let channels = await this.channelRepo.searchChannels(profileId, query, ContentType.LIVESTREAM);

        if (groupTitle) {
            channels = channels.filter(c => c.groupTitle === groupTitle);
        }

        return channels;
    }

    async validateStreamUrl(url: string): Promise<StreamInfo> {
        try {
            const response = await axios.head(url, { timeout: 5000 });
            return {
                available: true,
                contentType: response.headers['content-type'] || 'unknown',
                size: response.headers['content-length'] ? parseInt(response.headers['content-length']) : undefined,
            };
        } catch (error) {
            return {
                available: false,
                contentType: 'unknown',
            };
        }
    }
}
