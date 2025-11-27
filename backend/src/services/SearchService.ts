import { ChannelRepository } from '../repositories/ChannelRepository';
import { SeriesRepository } from '../repositories/SeriesRepository';
import { PrismaClient } from '@prisma/client';

export interface SearchFilters {
    contentTypes?: ('CHANNEL' | 'MOVIE' | 'SERIES')[];
    groupTitles?: string[];
    years?: number[];
    minDuration?: number;
    maxDuration?: number;
}

export interface SearchResult {
    channels: any[];
    movies: any[];
    series: any[];
    total: number;
}

export class SearchService {
    constructor(
        private prisma: PrismaClient,
        private channelRepo: ChannelRepository,
        private seriesRepo: SeriesRepository
    ) { }

    async globalSearch(
        profileId: string,
        query: string,
        filters?: SearchFilters,
        limit: number = 20
    ): Promise<SearchResult> {
        const searchQuery = query.toLowerCase().trim();

        if (searchQuery.length < 2) {
            throw new Error('Search query must be at least 2 characters');
        }

        const results: SearchResult = {
            channels: [],
            movies: [],
            series: [],
            total: 0,
        };

        // Search channels (livestreams)
        if (!filters?.contentTypes || filters.contentTypes.includes('CHANNEL')) {
            results.channels = await this.searchChannels(
                profileId,
                searchQuery,
                filters,
                limit
            );
        }

        // Search movies
        if (!filters?.contentTypes || filters.contentTypes.includes('MOVIE')) {
            results.movies = await this.searchMovies(
                profileId,
                searchQuery,
                filters,
                limit
            );
        }

        // Search series
        if (!filters?.contentTypes || filters.contentTypes.includes('SERIES')) {
            results.series = await this.searchSeries(
                profileId,
                searchQuery,
                filters,
                limit
            );
        }

        results.total = results.channels.length + results.movies.length + results.series.length;

        // Save search history
        await this.saveSearchHistory(profileId, query, filters, results.total);

        return results;
    }

    private async searchChannels(
        profileId: string,
        query: string,
        filters?: SearchFilters,
        limit: number = 20
    ) {
        const whereClause: any = {
            profileId,
            contentType: 'LIVESTREAM',
            OR: [
                { displayName: { contains: query } },
                { tvgName: { contains: query } },
            ],
        };

        if (filters?.groupTitles && filters.groupTitles.length > 0) {
            whereClause.groupTitle = { in: filters.groupTitles };
        }

        return this.prisma.channel.findMany({
            where: whereClause,
            take: limit,
            orderBy: { displayName: 'asc' },
        });
    }

    private async searchMovies(
        profileId: string,
        query: string,
        filters?: SearchFilters,
        limit: number = 20
    ) {
        const whereClause: any = {
            profileId,
            contentType: 'MOVIE',
            OR: [
                { displayName: { contains: query } },
                { tvgName: { contains: query } },
            ],
        };

        if (filters?.groupTitles && filters.groupTitles.length > 0) {
            whereClause.groupTitle = { in: filters.groupTitles };
        }

        const movies = await this.prisma.channel.findMany({
            where: whereClause,
            take: limit,
            orderBy: { displayName: 'asc' },
        });

        // Filter by year if specified
        if (filters?.years && filters.years.length > 0) {
            return movies.filter(movie => {
                const metadata = movie.metadata as any;
                const year = metadata?.year;
                return year && filters.years!.includes(year);
            });
        }

        return movies;
    }

    private async searchSeries(
        profileId: string,
        query: string,
        filters?: SearchFilters,
        limit: number = 20
    ) {
        const whereClause: any = {
            profileId,
            OR: [
                { name: { contains: query } },
                { normalizedName: { contains: query } },
            ],
        };

        if (filters?.groupTitles && filters.groupTitles.length > 0) {
            whereClause.groupTitle = { in: filters.groupTitles };
        }

        return this.prisma.series.findMany({
            where: whereClause,
            take: limit,
            orderBy: { name: 'asc' },
            include: {
                _count: {
                    select: { episodes: true },
                },
            },
        });
    }

    private async saveSearchHistory(
        profileId: string,
        query: string,
        filters: SearchFilters | undefined,
        resultCount: number
    ) {
        await this.prisma.searchHistory.create({
            data: {
                profileId,
                query,
                filters: JSON.stringify(filters || {}),
                resultCount,
            },
        });

        // Keep only last 50 searches per profile
        const searches = await this.prisma.searchHistory.findMany({
            where: { profileId },
            orderBy: { createdAt: 'desc' },
            skip: 50,
            select: { id: true },
        });

        if (searches.length > 0) {
            await this.prisma.searchHistory.deleteMany({
                where: {
                    id: { in: searches.map(s => s.id) },
                },
            });
        }
    }

    async getSearchHistory(profileId: string, limit: number = 10) {
        return this.prisma.searchHistory.findMany({
            where: { profileId },
            orderBy: { createdAt: 'desc' },
            take: limit,
            distinct: ['query'], // Only unique queries
        });
    }

    async clearSearchHistory(profileId: string) {
        await this.prisma.searchHistory.deleteMany({
            where: { profileId },
        });
    }

    async getPopularSearches(profileId: string, limit: number = 10) {
        const searches = await this.prisma.searchHistory.groupBy({
            by: ['query'],
            where: { profileId },
            _count: { query: true },
            orderBy: { _count: { query: 'desc' } },
            take: limit,
        });

        return searches.map(s => ({
            query: s.query,
            count: s._count.query,
        }));
    }

    async getSuggestions(profileId: string, partialQuery: string, limit: number = 5) {
        if (partialQuery.length < 2) return [];

        // Get suggestions from search history
        const historySuggestions = await this.prisma.searchHistory.findMany({
            where: {
                profileId,
                query: {
                    startsWith: partialQuery.toLowerCase(),
                },
            },
            orderBy: { createdAt: 'desc' },
            take: limit,
            distinct: ['query'],
            select: { query: true },
        });

        return historySuggestions.map(s => s.query);
    }
}
