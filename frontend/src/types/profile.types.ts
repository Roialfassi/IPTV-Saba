export interface Profile {
    id: string;
    name: string;
    avatar?: string;
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
    stats?: ProfileStats;
    m3uSources?: M3USource[];
}

export interface ProfileStats {
    totalChannels: number;
    totalMovies: number;
    totalSeries: number;
    totalEpisodes: number;
    m3uSourcesCount: number;
}

export interface M3USource {
    id: string;
    url: string;
    name?: string;
    lastStatus: 'PENDING' | 'FETCHING' | 'PARSING' | 'SUCCESS' | 'FAILED';
    lastFetched?: string;
    totalEntries?: number;
    error?: string;
}

export interface SyncResult {
    jobId: string;
    status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
}

export interface CreateProfileDto {
    name: string;
    avatar?: string;
}

export interface UpdateProfileDto {
    name?: string;
    avatar?: string;
    settings?: Record<string, any>;
}
