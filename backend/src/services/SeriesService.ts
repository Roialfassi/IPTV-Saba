import { SeriesRepository } from '../repositories/SeriesRepository';
import { EpisodeRepository } from '../repositories/EpisodeRepository';
import { Series, Episode } from '@prisma/client';
import { AppError } from '../middleware/errorHandler.middleware';
import { PaginatedResult } from './ChannelService';

export interface SeriesWithStats extends Series {
    totalEpisodes: number;
    totalSeasons: number;
    latestEpisode?: {
        seasonNumber: number;
        episodeNumber: number;
        title?: string;
    };
}

export interface SeriesWithEpisodes extends Series {
    seasons: {
        [seasonNumber: number]: Episode[];
    };
    totalEpisodes: number;
    totalSeasons: number;
}

export interface SeasonInfo {
    seasonNumber: number;
    episodeCount: number;
    episodes?: Episode[];
}

export class SeriesService {
    constructor(
        private seriesRepo: SeriesRepository,
        private episodeRepo: EpisodeRepository
    ) { }

    async getAllSeries(
        profileId: string,
        options: {
            page: number;
            limit: number;
            search?: string;
        }
    ): Promise<PaginatedResult<SeriesWithStats>> {
        const page = options.page || 1;
        const limit = options.limit || 50;

        let seriesList: Series[];

        if (options.search) {
            seriesList = await this.seriesRepo.searchSeries(profileId, options.search);
        } else {
            seriesList = await this.seriesRepo.findByProfileId(profileId);
        }

        // Pagination in memory if we fetched all (findByProfileId fetches all)
        // Ideally repo should support pagination
        const total = seriesList.length;
        const paginatedSeries = seriesList.slice((page - 1) * limit, page * limit);

        // Calculate stats for each series
        // This could be N+1 problem. Optimized approach: 
        // 1. Fetch all episodes for these series IDs (if not too many)
        // 2. Or assume we don't need exact counts for list view, or use a view/aggregation query
        // For now, doing it individually but parallelized
        const seriesWithStats = await Promise.all(
            paginatedSeries.map(s => this.calculateSeriesStats(s))
        );

        return {
            data: seriesWithStats,
            total,
            page,
            totalPages: Math.ceil(total / limit),
        };
    }

    async getSeriesById(
        profileId: string,
        seriesId: string
    ): Promise<SeriesWithEpisodes> {
        const series = await this.seriesRepo.findByIdWithEpisodes(seriesId);
        if (!series) {
            throw new AppError(404, 'Series not found');
        }
        if (series.profileId !== profileId) {
            throw new AppError(403, 'Series does not belong to this profile');
        }

        const episodes = series.episodes as Episode[];
        const seasons: { [key: number]: Episode[] } = {};
        const uniqueSeasons = new Set<number>();

        episodes.forEach(ep => {
            if (!seasons[ep.seasonNumber]) {
                seasons[ep.seasonNumber] = [];
                uniqueSeasons.add(ep.seasonNumber);
            }
            seasons[ep.seasonNumber].push(ep);
        });

        return {
            ...series,
            seasons,
            totalEpisodes: episodes.length,
            totalSeasons: uniqueSeasons.size,
        };
    }

    async getSeasons(
        profileId: string,
        seriesId: string
    ): Promise<SeasonInfo[]> {
        // Verify series exists/access
        const series = await this.seriesRepo.findById(seriesId);
        if (!series || series.profileId !== profileId) {
            throw new AppError(404, 'Series not found');
        }

        const episodes = await this.episodeRepo.findBySeriesId(seriesId);
        const seasonMap = new Map<number, number>();

        episodes.forEach(ep => {
            const count = seasonMap.get(ep.seasonNumber) || 0;
            seasonMap.set(ep.seasonNumber, count + 1);
        });

        const seasons: SeasonInfo[] = [];
        seasonMap.forEach((count, seasonNumber) => {
            seasons.push({ seasonNumber, episodeCount: count });
        });

        return seasons.sort((a, b) => a.seasonNumber - b.seasonNumber);
    }

    async searchSeries(
        profileId: string,
        query: string
    ): Promise<Series[]> {
        return this.seriesRepo.searchSeries(profileId, query);
    }

    private async calculateSeriesStats(series: Series): Promise<SeriesWithStats> {
        // This is expensive if done for every series in a list without optimized queries
        // Using episode repo to get counts
        const episodes = await this.episodeRepo.findBySeriesId(series.id);
        const uniqueSeasons = new Set(episodes.map(e => e.seasonNumber));

        let latestEpisode: Episode | undefined;
        if (episodes.length > 0) {
            latestEpisode = episodes[episodes.length - 1]; // Assuming sorted by repo
        }

        return {
            ...series,
            totalEpisodes: episodes.length,
            totalSeasons: uniqueSeasons.size,
            latestEpisode: latestEpisode ? {
                seasonNumber: latestEpisode.seasonNumber,
                episodeNumber: latestEpisode.episodeNumber,
                title: latestEpisode.title || undefined
            } : undefined
        };
    }
}
