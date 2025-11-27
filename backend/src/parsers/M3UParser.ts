import axios from 'axios';
import { randomUUID } from 'crypto';
import pLimit from 'p-limit';
import { M3UEntry, ParsedM3U, ParseError } from './m3u.types';
import { M3UValidator } from './M3UValidator';
import { logger } from '../utils/logger';

export class M3UParser {
    private static readonly TIMEOUT = 60000;
    private static readonly MAX_RETRIES = 3;
    private static readonly CONCURRENCY = 5;

    async downloadM3U(url: string): Promise<string> {
        let attempt = 0;
        while (attempt < M3UParser.MAX_RETRIES) {
            try {
                const response = await axios.get(url, {
                    timeout: M3UParser.TIMEOUT,
                    responseType: 'text',
                    validateStatus: (status) => status === 200,
                });
                return response.data;
            } catch (error: any) {
                attempt++;
                logger.warn(`Attempt ${attempt} failed for ${url}: ${error.message}`);
                if (attempt >= M3UParser.MAX_RETRIES) {
                    throw new Error(`Failed to download M3U after ${M3UParser.MAX_RETRIES} attempts: ${error.message}`);
                }
                await new Promise((resolve) => setTimeout(resolve, 1000 * Math.pow(2, attempt)));
            }
        }
        throw new Error('Unreachable code');
    }

    async parseM3U(content: string, sourceUrl: string = ''): Promise<ParsedM3U> {
        const lines = content.split(/\r?\n/);
        const entries: M3UEntry[] = [];
        const errors: ParseError[] = [];

        let currentMetadata = '';

        // Regex patterns
        const tvgIdRegex = /tvg-[Ii][Dd]="([^"]*)"/;
        const tvgNameRegex = /tvg-[Nn]ame="([^"]*)"/;
        const tvgLogoRegex = /tvg-[Ll]ogo="([^"]*)"/;
        const groupTitleRegex = /group-[Tt]itle="([^"]*)"/;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();

            if (!line) continue;

            if (line.startsWith('#EXTINF:')) {
                currentMetadata = line;
            } else if (!line.startsWith('#')) {
                // It's a URL
                if (!currentMetadata) {
                    // URL without metadata, skip or handle?
                    // For now, we skip as per requirements usually implying EXTINF exists
                    // But let's log it as error
                    errors.push({ line: i + 1, content: line, reason: 'URL without metadata' });
                    continue;
                }

                const url = line;

                // Extract metadata
                const tvgIdMatch = currentMetadata.match(tvgIdRegex);
                const tvgNameMatch = currentMetadata.match(tvgNameRegex);
                const tvgLogoMatch = currentMetadata.match(tvgLogoRegex);
                const groupTitleMatch = currentMetadata.match(groupTitleRegex);

                // Extract display name (everything after the last comma)
                const lastCommaIndex = currentMetadata.lastIndexOf(',');
                const displayName = lastCommaIndex !== -1 ? currentMetadata.substring(lastCommaIndex + 1).trim() : 'Unknown';

                const entry: M3UEntry = {
                    id: randomUUID(),
                    tvgId: tvgIdMatch ? tvgIdMatch[1] : '',
                    tvgName: tvgNameMatch ? tvgNameMatch[1] : '',
                    tvgLogo: tvgLogoMatch ? tvgLogoMatch[1] : '',
                    groupTitle: groupTitleMatch ? groupTitleMatch[1] : '',
                    displayName,
                    url,
                    rawMetadata: currentMetadata,
                };

                const validation = M3UValidator.validateEntry(entry);
                if (validation.isValid) {
                    entries.push(entry);
                } else {
                    errors.push({ line: i + 1, content: line, reason: validation.reason || 'Invalid entry' });
                }

                currentMetadata = ''; // Reset for next entry
            }
        }

        return {
            sourceUrl,
            entries,
            parsedAt: new Date(),
            totalEntries: entries.length,
            errors,
        };
    }

    async parseParallel(urls: string[]): Promise<ParsedM3U[]> {
        const limit = pLimit(M3UParser.CONCURRENCY);

        const promises = urls.map((url) =>
            limit(async () => {
                try {
                    const content = await this.downloadM3U(url);
                    return this.parseM3U(content, url);
                } catch (error: any) {
                    logger.error(`Failed to process ${url}: ${error.message}`);
                    // Return empty result with error? Or just null?
                    // Returning a "failed" ParsedM3U structure
                    return {
                        sourceUrl: url,
                        entries: [],
                        parsedAt: new Date(),
                        totalEntries: 0,
                        errors: [{ line: 0, content: '', reason: error.message }],
                    };
                }
            })
        );

        return Promise.all(promises);
    }
}
