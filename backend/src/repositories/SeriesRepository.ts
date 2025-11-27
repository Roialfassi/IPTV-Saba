import { PrismaClient, Series } from '@prisma/client';
import { BaseRepository } from './BaseRepository';

type SeriesWithEpisodes = Series & { episodes: any[] };

export class SeriesRepository extends BaseRepository<Series> {
    protected model: any;

    constructor(protected prisma: PrismaClient) {
        super();
        this.model = prisma.series;
    }

    async findByProfileId(profileId: string): Promise<Series[]> {
        return this.model.findMany({
            where: { profileId },
            orderBy: { name: 'asc' },
        });
    }

    async findByIdWithEpisodes(id: string): Promise<SeriesWithEpisodes | null> {
        return this.model.findUnique({
            where: { id },
            include: {
                episodes: {
                    orderBy: [
                        { seasonNumber: 'asc' },
                        { episodeNumber: 'asc' },
                    ],
                },
            },
        });
    }

    async findOrCreate(data: {
        name: string;
        normalizedName: string;
        profileId: string;
        logo?: string;
        groupTitle: string;
    }): Promise<Series> {
        const existing = await this.model.findUnique({
            where: {
                normalizedName_profileId: {
                    normalizedName: data.normalizedName,
                    profileId: data.profileId,
                },
            },
        });

        if (existing) {
            return existing;
        }

        return this.create(data);
    }

    async bulkCreateWithEpisodes(seriesData: any[]): Promise<number> {
        // Note: Prisma doesn't support deep nested createMany. 
        // We handle this transactionally in the service layer or iterate.
        // For now, returning 0 as placeholder or implementing loop.
        let count = 0;
        for (const series of seriesData) {
            await this.prisma.series.create({
                data: {
                    ...series,
                    episodes: {
                        create: series.episodes,
                    },
                },
            });
            count++;
        }
        return count;
    }

    async searchSeries(profileId: string, query: string): Promise<Series[]> {
        return this.model.findMany({
            where: {
                profileId,
                name: { contains: query },
            },
            take: 50,
        });
    }

    async deleteByProfile(profileId: string): Promise<number> {
        const result = await this.model.deleteMany({
            where: { profileId },
        });
        return result.count;
    }
}
