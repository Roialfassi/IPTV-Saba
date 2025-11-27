import { PrismaClient } from '@prisma/client';
import { ProfileRepository } from './ProfileRepository';
import { M3USourceRepository } from './M3USourceRepository';
import { ChannelRepository } from './ChannelRepository';
import { SeriesRepository } from './SeriesRepository';
import { EpisodeRepository } from './EpisodeRepository';
import { FavoritesRepository } from './FavoritesRepository';
import { WatchHistoryRepository } from './WatchHistoryRepository';

const prisma = new PrismaClient();

export const repositories = {
    profile: new ProfileRepository(prisma),
    m3uSource: new M3USourceRepository(prisma),
    channel: new ChannelRepository(prisma),
    series: new SeriesRepository(prisma),
    episode: new EpisodeRepository(prisma),
    favorites: new FavoritesRepository(prisma),
    history: new WatchHistoryRepository(prisma),
};

export const db = prisma;

export const transaction = async <T>(
    callback: (txRepositories: typeof repositories) => Promise<T>
): Promise<T> => {
    return prisma.$transaction(async (tx) => {
        // Create repositories bound to the transaction client
        const txRepos = {
            profile: new ProfileRepository(tx as any),
            m3uSource: new M3USourceRepository(tx as any),
            channel: new ChannelRepository(tx as any),
            series: new SeriesRepository(tx as any),
            episode: new EpisodeRepository(tx as any),
            favorites: new FavoritesRepository(tx as any),
            history: new WatchHistoryRepository(tx as any),
        };
        return callback(txRepos);
    });
};
