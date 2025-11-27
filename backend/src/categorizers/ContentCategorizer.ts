import { M3UEntry } from '../parsers/m3u.types';
import {
    CategorizedContent,
    CategorizedEntry,
    ContentType,
    MovieMetadata,
    SeriesEntry,
    SeriesMetadata,
    LivestreamMetadata,
} from '../types/content.types';

export class ContentCategorizer {
    // Regex patterns
    private static readonly SERIES_REGEX = /[Ss](\d+)[Ee](\d+)/;
    private static readonly SEASON_REGEX = /[Ss]eason\s*(\d+)/i;
    private static readonly EPISODE_REGEX = /[Ee]pisode?\s*(\d+)/i;
    private static readonly YEAR_REGEX = /\b(19|20)\d{2}\b/;
    private static readonly MOVIE_EXTENSIONS = ['.mp4', '.mkv', '.avi'];

    static categorize(entries: M3UEntry[]): CategorizedContent {
        const livestreams: CategorizedEntry[] = [];
        const movies: CategorizedEntry[] = [];
        const seriesMap = new Map<string, SeriesEntry>();

        for (const entry of entries) {
            const seriesInfo = this.extractSeriesInfo(entry.displayName) || this.extractSeriesInfo(entry.tvgName);

            if (seriesInfo) {
                // It's a series
                const categorizedEntry: CategorizedEntry = {
                    ...entry,
                    contentType: ContentType.SERIES,
                    metadata: seriesInfo,
                };

                // Group by series name
                const seriesName = seriesInfo.seriesName;
                if (!seriesMap.has(seriesName)) {
                    seriesMap.set(seriesName, {
                        seriesName,
                        logo: entry.tvgLogo,
                        groupTitle: entry.groupTitle,
                        episodes: [],
                    });
                }
                seriesMap.get(seriesName)!.episodes.push(categorizedEntry);
            } else if (this.isMovie(entry)) {
                // It's a movie
                const year = this.extractYear(entry.displayName) || this.extractYear(entry.tvgName);
                const title = this.extractTitle(entry.displayName);

                const metadata: MovieMetadata = {
                    title,
                    year: year || undefined,
                };

                movies.push({
                    ...entry,
                    contentType: ContentType.MOVIE,
                    metadata,
                });
            } else {
                // Default to livestream
                const metadata: LivestreamMetadata = {
                    channelName: entry.displayName,
                    category: entry.groupTitle,
                };

                livestreams.push({
                    ...entry,
                    contentType: ContentType.LIVESTREAM,
                    metadata,
                });
            }
        }

        return { livestreams, movies, series: seriesMap };
    }

    private static isMovie(entry: M3UEntry): boolean {
        // Check group title
        const groupLower = entry.groupTitle.toLowerCase();
        if (groupLower.includes('movie') || groupLower.includes('film') || groupLower.includes('cinema') || groupLower.includes('vod')) {
            return true;
        }

        // Check file extension
        if (this.MOVIE_EXTENSIONS.some(ext => entry.url.toLowerCase().endsWith(ext))) {
            // If it has movie extension and NOT series pattern, it's likely a movie
            return true;
        }

        // Check year pattern if not series
        if (this.YEAR_REGEX.test(entry.displayName)) {
            return true;
        }

        return false;
    }

    private static extractSeriesInfo(name: string): SeriesMetadata | null {
        // Check S##E## pattern
        const sMatch = name.match(this.SERIES_REGEX);
        if (sMatch) {
            const seasonNumber = parseInt(sMatch[1], 10);
            const episodeNumber = parseInt(sMatch[2], 10);
            const seriesName = this.normalizeSeriesName(name.substring(0, sMatch.index).trim());
            return { seriesName, seasonNumber, episodeNumber };
        }

        // Check Season X Episode Y pattern
        const seasonMatch = name.match(this.SEASON_REGEX);
        const episodeMatch = name.match(this.EPISODE_REGEX);

        if (seasonMatch && episodeMatch) {
            const seasonNumber = parseInt(seasonMatch[1], 10);
            const episodeNumber = parseInt(episodeMatch[1], 10);
            // This is harder to extract name cleanly without more complex logic, 
            // assuming name is at start
            const seriesName = this.normalizeSeriesName(name.split(/[Ss]eason/)[0].trim());
            return { seriesName, seasonNumber, episodeNumber };
        }

        return null;
    }

    private static extractYear(name: string): number | null {
        const match = name.match(this.YEAR_REGEX);
        return match ? parseInt(match[0], 10) : null;
    }

    private static extractTitle(name: string): string {
        // Remove year and extension
        let title = name.replace(this.YEAR_REGEX, '').trim();
        this.MOVIE_EXTENSIONS.forEach(ext => {
            if (title.toLowerCase().endsWith(ext)) {
                title = title.substring(0, title.length - ext.length);
            }
        });
        // Remove trailing punctuation
        return title.replace(/^[-_.\s]+|[-_.\s]+$/g, '');
    }

    private static normalizeSeriesName(name: string): string {
        return name.replace(/[._]/g, ' ').trim();
    }
}
