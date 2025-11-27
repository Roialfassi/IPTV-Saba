import { PrismaClient, M3USource } from '@prisma/client';
import { BaseRepository } from './BaseRepository';

export class M3USourceRepository extends BaseRepository<M3USource> {
    protected model: any;

    constructor(protected prisma: PrismaClient) {
        super();
        this.model = prisma.m3USource;
    }

    async findByProfileId(profileId: string): Promise<M3USource[]> {
        return this.model.findMany({
            where: { profileId },
            orderBy: { createdAt: 'desc' },
        });
    }

    async updateStatus(id: string, status: string, totalEntries?: number): Promise<M3USource> {
        const data: any = { lastStatus: status };
        if (totalEntries !== undefined) {
            data.totalEntries = totalEntries;
        }
        if (status === 'SUCCESS') {
            data.lastFetched = new Date();
        }
        return this.update(id, data);
    }

    async getSourcesNeedingRefresh(olderThan: Date): Promise<M3USource[]> {
        return this.model.findMany({
            where: {
                OR: [
                    { lastFetched: { lt: olderThan } },
                    { lastFetched: null },
                ],
            },
        });
    }
}
