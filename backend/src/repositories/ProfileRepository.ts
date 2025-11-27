import { PrismaClient, Profile } from '@prisma/client';
import { BaseRepository } from './BaseRepository';

export class ProfileRepository extends BaseRepository<Profile> {
    protected model: any;

    constructor(protected prisma: PrismaClient) {
        super();
        this.model = prisma.profile;
    }

    async findByIdWithSources(id: string) {
        return this.model.findUnique({
            where: { id },
            include: { m3uSources: true },
        });
    }

    async findActiveProfiles(): Promise<Profile[]> {
        return this.model.findMany({
            where: { isActive: true },
        });
    }

    async setActive(id: string, isActive: boolean): Promise<Profile> {
        return this.update(id, { isActive });
    }

    async getProfileStats(id: string) {
        const [channels, sources] = await Promise.all([
            this.prisma.channel.count({ where: { profileId: id } }),
            this.prisma.m3USource.count({ where: { profileId: id } }),
        ]);

        // Note: This is a simplified stats query. 
        // For detailed breakdown (movies, series), we'd need more specific queries.
        return {
            totalChannels: channels,
            totalSources: sources,
        };
    }
}
