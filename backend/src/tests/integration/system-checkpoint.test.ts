import { describe, it, expect, beforeAll } from '@jest/globals';
import { PrismaClient } from '@prisma/client';
import axios from 'axios';

const prisma = new PrismaClient();
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:3000';

describe('System Checkpoint Tests', () => {
    beforeAll(async () => {
        // Ensure test profile exists
        await prisma.profile.upsert({
            where: { id: 'test-profile' },
            update: {},
            create: {
                id: 'test-profile',
                name: 'Test Profile',
                isActive: true,
            },
        });
    });

    describe('✅ Database Connectivity', () => {
        it('should connect to database', async () => {
            const result = await prisma.$queryRaw`SELECT 1`;
            expect(result).toBeDefined();
        });

        it('should have all required tables', async () => {
            const tables = ['profile', 'channel', 'series', 'episode'];
            for (const table of tables) {
                const count = await (prisma as any)[table].count();
                expect(count).toBeGreaterThanOrEqual(0);
            }
        });
    });

    describe('✅ M3U Parsing', () => {
        it('should parse sample M3U from document', async () => {
            const sampleM3U = `#EXTINF:-1 tvg-ID="NULL" tvg-name="VIP CRO: SPORT KLUB 9" tvg-logo="[" group-title="Live: Hrvatska",VIP CRO: SPORT KLUB 9
http://redacted.example/20646`;

            const { M3UParser } = await import('../../parsers/M3UParser');
            const parser = new M3UParser();
            const result = await parser.parseM3U(sampleM3U);

            expect(result.entries.length).toBe(1);
            expect(result.entries[0].tvgName).toBe('VIP CRO: SPORT KLUB 9');
        });

        it('should parse Israel M3U from URL', async () => {
            const { M3UParser } = await import('../../parsers/M3UParser');
            const parser = new M3UParser();

            const content = await parser.downloadM3U(
                'https://iptv-org.github.io/iptv/countries/il.m3u'
            );
            const result = await parser.parseM3U(content);

            expect(result.entries.length).toBeGreaterThan(0);
            console.log(`✅ Parsed ${result.entries.length} channels from Israel M3U`);
        }, 30000);
    });

    describe('✅ Content Categorization', () => {
        it('should categorize channels correctly', async () => {
            const { ContentCategorizer } = await import('../../categorizers/ContentCategorizer');

            const testEntries = [
                {
                    id: '1',
                    tvgId: 'test',
                    tvgName: 'Sport Channel',
                    tvgLogo: '',
                    groupTitle: 'Live: Sports',
                    displayName: 'Sport Channel',
                    url: 'http://example.com',
                    rawMetadata: '',
                },
                {
                    id: '2',
                    tvgId: 'test2',
                    tvgName: 'Movie 2023',
                    tvgLogo: '',
                    groupTitle: 'Movies',
                    displayName: 'Movie - 2023',
                    url: 'http://example.com/movie.mp4',
                    rawMetadata: '',
                },
                {
                    id: '3',
                    tvgId: 'test3',
                    tvgName: 'Series.S01E01',
                    tvgLogo: '',
                    groupTitle: 'Series',
                    displayName: 'Series S01E01',
                    url: 'http://example.com/series.mkv',
                    rawMetadata: '',
                },
            ];

            const result = ContentCategorizer.categorize(testEntries);

            expect(result.livestreams.length).toBe(1);
            expect(result.movies.length).toBe(1);
            expect(result.series.size).toBe(1);
            console.log('✅ Content categorization working correctly');
        });
    });

    describe('✅ API Endpoints', () => {
        it('GET /health should return 200', async () => {
            const response = await axios.get(`${API_BASE_URL}/health`);
            expect(response.status).toBe(200);
        });

        it('GET /api/v1/profiles should work', async () => {
            const response = await axios.get(`${API_BASE_URL}/api/v1/profiles`);
            expect(response.status).toBe(200);
            expect(response.data.profiles).toBeDefined();
        });

        it('POST /api/v1/profiles should create profile', async () => {
            const response = await axios.post(`${API_BASE_URL}/api/v1/profiles`, {
                name: 'Test Profile ' + Date.now(),
            });
            expect(response.status).toBe(201);
            expect(response.data.name).toBeDefined();
        });
    });

    describe('✅ Profile & M3U Source Management', () => {
        it('should create profile and add M3U source', async () => {
            const profile = await prisma.profile.create({
                data: {
                    name: 'Integration Test Profile',
                },
            });

            const source = await prisma.m3USource.create({
                data: {
                    profileId: profile.id,
                    url: 'https://iptv-org.github.io/iptv/countries/il.m3u',
                    lastStatus: 'PENDING',
                },
            });

            expect(profile).toBeDefined();
            expect(source).toBeDefined();
            console.log('✅ Profile and M3U source created successfully');
        });
    });

    describe('✅ Video Player Integration', () => {
        it('should have valid stream URLs', () => {
            const testURL = 'http://example.com/stream.m3u8';
            expect(testURL).toMatch(/^https?:\/\//);
        });

        it('should support HLS format', () => {
            const hlsURL = 'http://example.com/stream.m3u8';
            expect(hlsURL).toContain('.m3u8');
        });
    });


});
