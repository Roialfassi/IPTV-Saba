import { PrismaClient, Favorite } from '@prisma/client';

export class FavoritesRepository {
    constructor(private prisma: PrismaClient) { }

    async findByProfile(
        profileId: string,
        contentType?: string,
        skip?: number,
        take?: number
    ): Promise<Favorite[]> {
        return this.prisma.favorite.findMany({
            where: {
                profileId,
                ...(contentType && { contentType }),
            },
            orderBy: { createdAt: 'desc' },
            skip,
            take,
        });
    }

    async findOne(
        profileId: string,
        contentType: string,
        contentId: string
    ): Promise<Favorite | null> {
        return this.prisma.favorite.findUnique({
            where: {
                profileId_contentType_contentId: {
                    profileId,
                    contentType,
                    contentId,
                },
            },
        });
    }

    async create(data: {
        profileId: string;
        contentType: string;
        contentId: string;
        title: string;
        logo?: string;
        url?: string;
    }): Promise<Favorite> {
        return this.prisma.favorite.create({ data });
    }

    async delete(id: string): Promise<void> {
        await this.prisma.favorite.delete({ where: { id } });
    }

    async deleteByContent(
        profileId: string,
        contentType: string,
        contentId: string
    ): Promise<void> {
        await this.prisma.favorite.deleteMany({
            where: { profileId, contentType, contentId },
        });
    }

    async count(profileId: string, contentType?: string): Promise<number> {
        return this.prisma.favorite.count({
            where: {
                profileId,
                ...(contentType && { contentType }),
            },
        });
    }

    async isFavorite(
        profileId: string,
        contentType: string,
        contentId: string
    ): Promise<boolean> {
        const count = await this.prisma.favorite.count({
            where: { profileId, contentType, contentId },
        });
        return count > 0;
    }
}
