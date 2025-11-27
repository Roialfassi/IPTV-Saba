import { M3UEntry } from '../parsers/m3u.types';

export enum ContentType {
    LIVESTREAM = 'LIVESTREAM',
    MOVIE = 'MOVIE',
    SERIES = 'SERIES',
}

export interface SeriesMetadata {
    seriesName: string;
    seasonNumber: number;
    episodeNumber: number;
    episodeTitle?: string;
}

export interface MovieMetadata {
    title: string;
    year?: number;
    genre?: string;
}

export interface LivestreamMetadata {
    channelName: string;
    category: string; // from group-title
}

export interface CategorizedEntry extends M3UEntry {
    contentType: ContentType;
    metadata: SeriesMetadata | MovieMetadata | LivestreamMetadata;
}

export interface SeriesEntry {
    seriesName: string;
    logo: string;
    groupTitle: string;
    episodes: CategorizedEntry[];
}

export interface CategorizedContent {
    livestreams: CategorizedEntry[];
    movies: CategorizedEntry[];
    series: Map<string, SeriesEntry>; // grouped by series name
}
export interface WatchHistory {
    id: string;
    profileId: string;
    contentType: 'CHANNEL' | 'MOVIE' | 'EPISODE';
    contentId: string;
    title: string;
    logo?: string;
    url: string;
    progress: number;
    duration: number;
    seriesId?: string;
    seriesName?: string;
    seasonNumber?: number;
    episodeNumber?: number;
    createdAt: Date;
    updatedAt: Date;
}