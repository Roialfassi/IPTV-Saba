import type { Channel } from './channel.types';

export interface MovieMetadata {
    title?: string;
    year?: number;
    genre?: string[];
    director?: string;
    cast?: string[];
    plot?: string;
    rating?: number;
    duration?: number;
}

export interface Movie extends Channel {
    parsedMetadata: MovieMetadata;
}
