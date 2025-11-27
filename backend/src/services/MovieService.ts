import { ChannelRepository } from '../repositories/ChannelRepository';
import { Channel } from '@prisma/client';
import { AppError } from '../middleware/errorHandler.middleware';
import { ContentType, MovieMetadata } from '../types/content.types';
import { PaginatedResult } from './ChannelService';

export interface MovieWithMetadata extends Channel {
    parsedMetadata: MovieMetadata;
}

export class MovieService {
    constructor(private channelRepo: ChannelRepository) { }

    async getMovies(
        profileId: string,
        options: {
            page: number;
            limit: number;
            groupTitle?: string;
            year?: number;
            sortBy?: 'name' | 'year' | 'date';
            order?: 'asc' | 'desc';
        }
    ): Promise<PaginatedResult<MovieWithMetadata>> {
        // Fetch all movies for profile (filtering by groupTitle if provided)
        // Note: Since we need to parse metadata for year filtering/sorting, we might need to fetch more and filter in memory
        // OR we rely on database if we store metadata as JSONB and can query it (Prisma supports this but it's complex with generic JSON)
        // For now, fetching all movies in category and filtering in memory if year is involved or sorting by year

        // If only basic filters (groupTitle), we can use repo pagination
        // But if sorting by year, we need to fetch all, parse, sort, then paginate

        const page = options.page || 1;
        const limit = options.limit || 50;

        // Fetch all movies for the profile to handle complex sort/filter
        // TODO: Optimize this by pushing year/metadata into separate columns or using JSONB queries
        let movies = await this.channelRepo.findByProfileAndType(profileId, ContentType.MOVIE);

        if (options.groupTitle) {
            movies = movies.filter(m => m.groupTitle === options.groupTitle);
        }

        // Parse metadata
        let moviesWithMeta: MovieWithMetadata[] = movies.map(m => this.parseMovieMetadata(m));

        // Filter by year
        if (options.year) {
            moviesWithMeta = moviesWithMeta.filter(m => m.parsedMetadata.year === options.year);
        }

        // Sort
        const order = options.order === 'desc' ? -1 : 1;
        moviesWithMeta.sort((a, b) => {
            if (options.sortBy === 'year') {
                const yearA = a.parsedMetadata.year || 0;
                const yearB = b.parsedMetadata.year || 0;
                return (yearA - yearB) * order;
            } else if (options.sortBy === 'date') {
                return (a.createdAt.getTime() - b.createdAt.getTime()) * order;
            } else {
                // Default name
                return a.displayName.localeCompare(b.displayName) * order;
            }
        });

        // Paginate
        const total = moviesWithMeta.length;
        const paginated = moviesWithMeta.slice((page - 1) * limit, page * limit);

        return {
            data: paginated,
            total,
            page,
            totalPages: Math.ceil(total / limit),
        };
    }

    async getMovieById(
        profileId: string,
        movieId: string
    ): Promise<MovieWithMetadata> {
        const channel = await this.channelRepo.findById(movieId);
        if (!channel) {
            throw new AppError(404, 'Movie not found');
        }
        if (channel.profileId !== profileId) {
            throw new AppError(403, 'Movie does not belong to this profile');
        }
        if (channel.contentType !== ContentType.MOVIE) {
            throw new AppError(400, 'Channel is not a movie');
        }
        return this.parseMovieMetadata(channel);
    }

    async getMovieGroups(profileId: string): Promise<string[]> {
        return this.channelRepo.getGroupTitles(profileId, ContentType.MOVIE);
    }

    async getAvailableYears(profileId: string): Promise<number[]> {
        const movies = await this.channelRepo.findByProfileAndType(profileId, ContentType.MOVIE);
        const years = new Set<number>();

        movies.forEach(m => {
            const meta = this.parseMovieMetadata(m);
            if (meta.parsedMetadata.year) {
                years.add(meta.parsedMetadata.year);
            }
        });

        return Array.from(years).sort((a, b) => b - a);
    }

    async searchMovies(
        profileId: string,
        query: string,
        filters?: {
            year?: number;
            groupTitle?: string;
        }
    ): Promise<MovieWithMetadata[]> {
        let movies = await this.channelRepo.searchChannels(profileId, query, ContentType.MOVIE);

        if (filters?.groupTitle) {
            movies = movies.filter(m => m.groupTitle === filters.groupTitle);
        }

        let moviesWithMeta = movies.map(m => this.parseMovieMetadata(m));

        if (filters?.year) {
            moviesWithMeta = moviesWithMeta.filter(m => m.parsedMetadata.year === filters.year);
        }

        return moviesWithMeta;
    }

    private parseMovieMetadata(channel: Channel): MovieWithMetadata {
        // The metadata is stored as JSON in the database
        // We cast it to MovieMetadata
        const metadata = channel.metadata as unknown as MovieMetadata;

        // Ensure defaults
        const parsedMetadata: MovieMetadata = {
            title: metadata.title || channel.displayName,
            year: metadata.year,
            genre: metadata.genre
        };

        return {
            ...channel,
            parsedMetadata,
        };
    }
}
