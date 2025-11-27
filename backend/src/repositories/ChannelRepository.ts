import { PrismaClient, Channel, Prisma } from '@prisma/client';
import { BaseRepository } from './BaseRepository';

export class ChannelRepository extends BaseRepository<Channel> {
    protected model: any;

    constructor(protected prisma: PrismaClient) {
        super();
        this.model = prisma.channel;
    }

    async findByProfileAndType(
        profileId: string,
        contentType: string,
        skip?: number,
        take?: number
    ): Promise<Channel[]> {
        return this.model.findMany({
            where: {
                profileId,
                contentType,
            },
            skip,
            take,
            orderBy: { displayName: 'asc' },
        });
    }

    async findByGroupTitle(
        profileId: string,
        groupTitle: string
    ): Promise<Channel[]> {
        return this.model.findMany({
            where: {
                profileId,
                groupTitle,
            },
            orderBy: { displayName: 'asc' },
        });
    }

    async bulkCreate(channels: Omit<Channel, 'id' | 'createdAt'>[]): Promise<number> {
        const result = await this.model.createMany({
            data: channels,
        });
        return result.count;
    }

    async deleteByProfile(profileId: string): Promise<number> {
        const result = await this.model.deleteMany({
            where: { profileId },
        });
        return result.count;
    }

    async searchChannels(
        profileId: string,
        query: string,
        contentType?: string
    ): Promise<Channel[]> {
        const where: Prisma.ChannelWhereInput = {
            profileId,
            OR: [
                { displayName: { contains: query } },
                { tvgName: { contains: query } },
            ],
        };

        if (contentType) {
            where.contentType = contentType;
        }

        return this.model.findMany({
            where,
            take: 50,
        });
    }

    async getGroupTitles(profileId: string, contentType: string): Promise<string[]> {
        const results = await this.model.findMany({
            where: {
                profileId,
                contentType,
            },
            select: {
                groupTitle: true,
            },
            distinct: ['groupTitle'],
            orderBy: {
                groupTitle: 'asc',
            },
        });
        return results.map((r: { groupTitle: string }) => r.groupTitle);
    }
}
