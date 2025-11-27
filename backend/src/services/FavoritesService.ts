import { FavoritesRepository } from '../repositories/FavoritesRepository';
import { ChannelRepository } from '../repositories/ChannelRepository';
import { SeriesRepository } from '../repositories/SeriesRepository';

export class FavoritesService {
    constructor(
        private favoritesRepo: FavoritesRepository,
        private channelRepo: ChannelRepository,
        private seriesRepo: SeriesRepository
    ) { }

    async getFavorites(
        profileId: string,
        contentType?: string,
        page: number = 1,
        limit: number = 20
    ) {
        const skip = (page - 1) * limit;
        const [favorites, total] = await Promise.all([
            this.favoritesRepo.findByProfile(profileId, contentType, skip, limit),
            this.favoritesRepo.count(profileId, contentType),
        ]);

        return {
            favorites,
            total,
            page,
            totalPages: Math.ceil(total / limit),
        };
    }

    async addFavorite(
        profileId: string,
        contentType: 'CHANNEL' | 'MOVIE' | 'SERIES',
        contentId: string
    ) {
        // Check if already favorited
        const existing = await this.favoritesRepo.findOne(
            profileId,
            contentType,
            contentId
        );
        if (existing) {
            return existing;
        }

        // Fetch content details
        let title: string;
        let logo: string | undefined;
        let url: string | undefined;

        if (contentType === 'CHANNEL' || contentType === 'MOVIE') {
            const content = await this.channelRepo.findById(contentId);
            if (!content) {
                throw new Error('Content not found');
            }
            title = content.displayName;
            logo = content.logo || undefined;
            url = content.url;
        } else if (contentType === 'SERIES') {
            const series = await this.seriesRepo.findById(contentId);
            if (!series) {
                throw new Error('Series not found');
            }
            title = series.name;
            logo = series.logo || undefined;
        } else {
            throw new Error('Invalid content type');
        }

        return this.favoritesRepo.create({
            profileId,
            contentType,
            contentId,
            title,
            logo,
            url,
        });
    }

    async removeFavorite(
        profileId: string,
        contentType: string,
        contentId: string
    ) {
        await this.favoritesRepo.deleteByContent(profileId, contentType, contentId);
    }

    async isFavorite(
        profileId: string,
        contentType: string,
        contentId: string
    ): Promise<boolean> {
        return this.favoritesRepo.isFavorite(profileId, contentType, contentId);
    }

    async getFavoriteCounts(profileId: string) {
        const [channels, movies, series] = await Promise.all([
            this.favoritesRepo.count(profileId, 'CHANNEL'),
            this.favoritesRepo.count(profileId, 'MOVIE'),
            this.favoritesRepo.count(profileId, 'SERIES'),
        ]);

        return { channels, movies, series, total: channels + movies + series };
    }
}
