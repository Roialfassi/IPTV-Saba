import { M3UParser } from '../parsers/M3UParser';
import { ContentCategorizer } from '../categorizers/ContentCategorizer';
import { ChannelRepository } from '../repositories/ChannelRepository';
import { SeriesRepository } from '../repositories/SeriesRepository';
import { EpisodeRepository } from '../repositories/EpisodeRepository';
import { M3USourceRepository } from '../repositories/M3USourceRepository';
import { transaction } from '../repositories';
import { logger } from '../utils/logger';
import { ContentType, CategorizedEntry, SeriesEntry } from '../types/content.types';
import { Channel, Episode, Series } from '@prisma/client';

export interface SyncResult {
    success: boolean;
    totalEntries: number;
    categorized: {
        livestreams: number;
        movies: number;
        series: number;
        episodes: number;
    };
    duration: number; // ms
    errors?: string[];
}

export class M3USyncJob {
    constructor(
        private m3uParser: M3UParser,
        private categorizer: ContentCategorizer,
        private channelRepo: ChannelRepository,
        private seriesRepo: SeriesRepository,
        private episodeRepo: EpisodeRepository,
        private m3uSourceRepo: M3USourceRepository
    ) { }

    async execute(sourceId: string): Promise<SyncResult> {
        const startTime = Date.now();
        logger.info(`Starting sync for source ${sourceId}`);

        try {
            // 1. Fetch M3U source
            const source = await this.m3uSourceRepo.findById(sourceId);
            if (!source) {
                throw new Error(`Source ${sourceId} not found`);
            }

            // 2. Update status to FETCHING
            await this.m3uSourceRepo.updateStatus(sourceId, 'FETCHING');

            // 3. Download M3U file
            const m3uContent = await this.m3uParser.downloadM3U(source.url);

            // 4. Update status to PARSING
            await this.m3uSourceRepo.updateStatus(sourceId, 'PARSING');

            // 5. Parse M3U content
            const parsedM3U = await this.m3uParser.parseM3U(m3uContent, source.url);

            // 6. Categorize content
            // Note: ContentCategorizer.categorize is static, but we injected instance in constructor?
            // The previous implementation of ContentCategorizer had static methods.
            // We can use the class directly or the instance if we change it.
            // Assuming static usage based on previous file content.
            const categorized = ContentCategorizer.categorize(parsedM3U.entries);

            // 7. Delete old content
            await transaction(async (txRepos) => {
                await txRepos.channel.deleteByProfile(source.profileId);
                // @ts-ignore
                await txRepos.series['model'].deleteMany({ where: { profileId: source.profileId } });
            });

            // 8. Insert channels (movies + livestreams)
            const channelsToInsert = [
                ...categorized.livestreams.map(c => ({
                    tvgId: c.tvgId,
                    tvgName: c.tvgName,
                    displayName: c.displayName,
                    logo: c.tvgLogo,
                    url: c.url,
                    groupTitle: c.groupTitle,
                    contentType: ContentType.LIVESTREAM,
                    metadata: JSON.stringify(c.metadata),
                    profileId: source.profileId,
                })),
                ...categorized.movies.map(c => ({
                    tvgId: c.tvgId,
                    tvgName: c.tvgName,
                    displayName: c.displayName,
                    logo: c.tvgLogo,
                    url: c.url,
                    groupTitle: c.groupTitle,
                    contentType: ContentType.MOVIE,
                    metadata: JSON.stringify(c.metadata),
                    profileId: source.profileId,
                }))
            ];

            // Bulk insert channels in chunks
            const chunkSize = 500; // Smaller chunk size for SQLite
            for (let i = 0; i < channelsToInsert.length; i += chunkSize) {
                // Check if source still exists (it might have been deleted)
                const currentSource = await this.m3uSourceRepo.findById(sourceId);
                if (!currentSource) {
                    logger.info(`Source ${sourceId} was deleted, aborting sync`);
                    return {
                        success: false,
                        totalEntries: 0,
                        categorized: { livestreams: 0, movies: 0, series: 0, episodes: 0 },
                        duration: Date.now() - startTime,
                        errors: ['Source deleted during sync'],
                    };
                }

                const chunk = channelsToInsert.slice(i, i + chunkSize);
                await this.channelRepo.bulkCreate(chunk);
            }

            // 9. Insert series with episodes
            for (const [seriesName, seriesEntry] of categorized.series) {
                // Check if source still exists
                const currentSource = await this.m3uSourceRepo.findById(sourceId);
                if (!currentSource) {
                    logger.info(`Source ${sourceId} was deleted, aborting sync`);
                    return {
                        success: false,
                        totalEntries: 0,
                        categorized: { livestreams: 0, movies: 0, series: 0, episodes: 0 },
                        duration: Date.now() - startTime,
                        errors: ['Source deleted during sync'],
                    };
                }

                // Create series
                const series = await this.seriesRepo.create({
                    name: seriesEntry.seriesName,
                    normalizedName: seriesEntry.seriesName.toLowerCase(),
                    logo: seriesEntry.logo,
                    groupTitle: seriesEntry.groupTitle,
                    profileId: source.profileId,
                });

                // Create episodes
                const episodesToInsert = seriesEntry.episodes.map(ep => ({
                    seriesId: series.id,
                    seasonNumber: (ep.metadata as any).seasonNumber,
                    episodeNumber: (ep.metadata as any).episodeNumber,
                    title: (ep.metadata as any).episodeTitle || `Episode ${(ep.metadata as any).episodeNumber}`,
                    url: ep.url,
                    tvgName: ep.tvgName,
                }));

                // Bulk insert episodes in chunks if needed, but usually series aren't that huge
                // EpisodeRepo.bulkCreate already handles duplicates
                await this.episodeRepo.bulkCreate(episodesToInsert);
            }

            // 10. Update M3U source
            await this.m3uSourceRepo.updateStatus(sourceId, 'SUCCESS', parsedM3U.totalEntries);

            const duration = Date.now() - startTime;
            logger.info(`Sync completed for source ${sourceId} in ${duration}ms`);

            return {
                success: true,
                totalEntries: parsedM3U.totalEntries,
                categorized: {
                    livestreams: categorized.livestreams.length,
                    movies: categorized.movies.length,
                    series: categorized.series.size,
                    episodes: Array.from(categorized.series.values()).reduce((acc, s) => acc + s.episodes.length, 0),
                },
                duration,
            };

        } catch (error: any) {
            logger.error(`Sync failed for source ${sourceId}: ${error.message}`);
            await this.m3uSourceRepo.updateStatus(sourceId, 'FAILED');
            return {
                success: false,
                totalEntries: 0,
                categorized: { livestreams: 0, movies: 0, series: 0, episodes: 0 },
                duration: Date.now() - startTime,
                errors: [error.message],
            };
        }
    }
}
