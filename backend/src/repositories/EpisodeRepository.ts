import { PrismaClient, Episode } from '@prisma/client';
import { BaseRepository } from './BaseRepository';

export class EpisodeRepository extends BaseRepository<Episode> {
    protected model: any;

    constructor(protected prisma: PrismaClient) {
        super();
        this.model = prisma.episode;
    }

    async findBySeriesId(seriesId: string): Promise<Episode[]> {
        return this.model.findMany({
            where: { seriesId },
            orderBy: [
                { seasonNumber: 'asc' },
                { episodeNumber: 'asc' },
            ],
        });
    }

    async findBySeason(seriesId: string, seasonNumber: number): Promise<Episode[]> {
        return this.model.findMany({
            where: {
                seriesId,
                seasonNumber,
            },
            orderBy: { episodeNumber: 'asc' },
        });
    }

    async findEpisode(
        seriesId: string,
        seasonNumber: number,
        episodeNumber: number
    ): Promise<Episode | null> {
        return this.model.findUnique({
            where: {
                seriesId_seasonNumber_episodeNumber: {
                    seriesId,
                    seasonNumber,
                    episodeNumber,
                },
            },
        });
    }

    async bulkCreate(episodes: Omit<Episode, 'id' | 'createdAt'>[]): Promise<number> {
        if (episodes.length === 0) return 0;

        // Group by seriesId to minimize queries
        const seriesIds = [...new Set(episodes.map(e => e.seriesId))];
        let createdCount = 0;

        for (const seriesId of seriesIds) {
            const seriesEpisodes = episodes.filter(e => e.seriesId === seriesId);

            // Deduplicate incoming episodes for this series
            const uniqueEpisodes = new Map();
            for (const ep of seriesEpisodes) {
                const key = `${ep.seasonNumber}-${ep.episodeNumber}`;
                if (!uniqueEpisodes.has(key)) {
                    uniqueEpisodes.set(key, ep);
                }
            }
            const deduplicatedEpisodes = Array.from(uniqueEpisodes.values());

            // Get existing episodes for this series
            const existing = await this.model.findMany({
                where: { seriesId },
                select: { seasonNumber: true, episodeNumber: true }
            });

            // Create a set of existing S-E keys
            const existingSet = new Set(existing.map((e: any) => `${e.seasonNumber}-${e.episodeNumber}`));

            // Filter out duplicates
            const newEpisodes = deduplicatedEpisodes.filter(e => !existingSet.has(`${e.seasonNumber}-${e.episodeNumber}`));

            if (newEpisodes.length > 0) {
                const result = await this.model.createMany({
                    data: newEpisodes,
                });
                createdCount += result.count;
            }
        }

        return createdCount;
    }

    async getSeasonNumbers(seriesId: string): Promise<number[]> {
        const results = await this.model.findMany({
            where: { seriesId },
            select: { seasonNumber: true },
            distinct: ['seasonNumber'],
            orderBy: { seasonNumber: 'asc' },
        });
        return results.map((r: { seasonNumber: number }) => r.seasonNumber);
    }
}
