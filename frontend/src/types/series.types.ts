export interface Episode {
    id: string;
    seriesId: string;
    seasonNumber: number;
    episodeNumber: number;
    title: string;
    url: string;
    tvgName?: string;
    duration?: number;
    plot?: string;
    rating?: number;
    releaseDate?: string;
}

export interface Series {
    id: string;
    name: string;
    normalizedName: string;
    logo?: string;
    groupTitle?: string;
    profileId: string;
    totalEpisodes?: number;
    totalSeasons?: number;
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
}

export interface SeasonInfo {
    seasonNumber: number;
    episodeCount: number;
    episodes?: Episode[];
}
