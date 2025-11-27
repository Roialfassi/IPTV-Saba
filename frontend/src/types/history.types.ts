export interface WatchHistory {
    id: string;
    profileId: string;
    contentType: 'CHANNEL' | 'MOVIE' | 'EPISODE';
    contentId: string;
    title: string;
    logo?: string;
    url: string;
    seriesId?: string;
    seriesName?: string;
    seasonNumber?: number;
    episodeNumber?: number;
    watchedAt: string;
    progress: number;
    duration: number;
}

export interface HistoryResponse {
    history: WatchHistory[];
    total: number;
    page: number;
    totalPages: number;
}

export interface UpdateProgressData {
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
}
