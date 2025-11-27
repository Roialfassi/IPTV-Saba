import { PrismaClient, WatchHistory } from '@prisma/client';

export class WatchHistoryRepository {
    constructor(private prisma: PrismaClient) { }

    async findByProfile(
        profileId: string,
        skip?: number,
        take?: number
    ): Promise<WatchHistory[]> {
        return this.prisma.watchHistory.findMany({
            where: { profileId },
            orderBy: { watchedAt: 'desc' },
            skip,
            take,
        });
    }

    async findOne(
        profileId: string,
        contentType: string,
        contentId: string
    ): Promise<WatchHistory | null> {
        return this.prisma.watchHistory.findUnique({
            where: {
                profileId_contentType_contentId: {
                    profileId,
                    contentType,
                    contentId,
                },
            },
        });
    }

    async upsert(data: {
        profileId: string;
        contentType: string;
        contentId: string;
        title: string;
        logo?: string;
        url: string;
        seriesId?: string;
        seriesName?: string;
        seasonNumber?: number;
        episodeNumber?: number;
        progress: number;
        duration: number;
    }): Promise<WatchHistory> {
        return this.prisma.watchHistory.upsert({
            where: {
                profileId_contentType_contentId: {
                    profileId: data.profileId,
                    contentType: data.contentType,
                    contentId: data.contentId,
                },
            },
            update: {
                progress: data.progress,
                duration: data.duration,
                watchedAt: new Date(),
            },
            create: data,
        });
    }

    async delete(id: string): Promise<void> {
        await this.prisma.watchHistory.delete({ where: { id } });
    }

    async deleteAll(profileId: string): Promise<number> {
        const result = await this.prisma.watchHistory.deleteMany({
            where: { profileId },
        });
        return result.count;
    }

    async getContinueWatching(
        profileId: string,
        limit: number = 10
    ): Promise<WatchHistory[]> {
        // Simplified version - SQLite doesn't support dynamic field comparisons in WHERE
        const allHistory = await this.prisma.watchHistory.findMany({
            where: {
                profileId,
                progress: { gt: 30 }, // At least 30 seconds watched
            },
            orderBy: { watchedAt: 'desc' },
        });

        // Filter in memory for completion check
        const continueWatching = allHistory.filter(item => {
            if (item.duration === 0) return true;
            const percentWatched = (item.progress / item.duration) * 100;
            return percentWatched < 95;
        });

        return continueWatching.slice(0, limit);
    }

    async count(profileId: string): Promise<number> {
        return this.prisma.watchHistory.count({ where: { profileId } });
    }
}
