export interface Channel {
    id: string;
    tvgId?: string;
    tvgName?: string;
    displayName: string;
    logo?: string;
    groupTitle?: string;
    url: string;
    contentType: 'LIVESTREAM' | 'MOVIE' | 'SERIES';
    isFavorite: boolean;
    profileId: string;
}

export interface PaginatedResult<T> {
    data: T[];
    total: number;
    page: number;
    totalPages: number;
}

export type PaginatedResponse<T> = PaginatedResult<T>;
