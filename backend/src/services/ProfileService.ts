import { ProfileRepository } from '../repositories/ProfileRepository';
import { M3USourceRepository } from '../repositories/M3USourceRepository';
import { M3USyncJob, SyncResult } from '../jobs/M3USyncJob';
import { Profile, M3USource } from '@prisma/client';
import { AppError } from '../middleware/errorHandler.middleware';
import { transaction } from '../repositories';

export interface ProfileWithStats extends Profile {
    stats: {
        totalChannels: number;
        totalSources: number; // Fixed from interface mismatch
    };
}

export interface ProfileWithDetails extends ProfileWithStats {
    m3uSources: M3USource[];
}

export interface SourceSyncStatus {
    status: string; // Fixed type to match Prisma string or union
    lastFetched: Date | null;
    totalEntries: number;
    errors?: string[];
}

export class ProfileService {
    constructor(
        private profileRepo: ProfileRepository,
        private m3uSourceRepo: M3USourceRepository,
        private m3uSyncJob: M3USyncJob
    ) { }

    async getAllProfiles(): Promise<ProfileWithStats[]> {
        const profiles = await this.profileRepo.findAll();

        // Enrich with stats
        const profilesWithStats = await Promise.all(
            profiles.map(async (p) => {
                const stats = await this.profileRepo.getProfileStats(p.id);
                return { ...p, stats };
            })
        );

        return profilesWithStats;
    }

    async getProfileById(id: string): Promise<ProfileWithDetails> {
        const profile = await this.profileRepo.findByIdWithSources(id);
        if (!profile) {
            throw new AppError(404, 'Profile not found');
        }

        const stats = await this.profileRepo.getProfileStats(id);

        return {
            ...profile,
            stats,
        };
    }

    async createProfile(data: { name: string; avatar?: string }): Promise<Profile> {
        const count = await this.profileRepo.count();
        const isActive = count === 0; // First profile is active by default

        return this.profileRepo.create({
            ...data,
            isActive,
        });
    }

    async updateProfile(id: string, data: Partial<Profile>): Promise<Profile> {
        const profile = await this.profileRepo.findById(id);
        if (!profile) {
            throw new AppError(404, 'Profile not found');
        }
        return this.profileRepo.update(id, data);
    }

    async deleteProfile(id: string): Promise<void> {
        const profile = await this.profileRepo.findById(id);
        if (!profile) {
            throw new AppError(404, 'Profile not found');
        }

        await transaction(async (txRepos) => {
            await txRepos.profile.delete(id);

            // If deleted profile was active, activate another one
            if (profile.isActive) {
                const remaining = await txRepos.profile.findAll(0, 1);
                if (remaining.length > 0) {
                    await txRepos.profile.setActive(remaining[0].id, true);
                }
            }
        });
    }

    async setActiveProfile(id: string): Promise<Profile> {
        const profile = await this.profileRepo.findById(id);
        if (!profile) {
            throw new AppError(404, 'Profile not found');
        }

        // Deactivate all, then activate one
        // Ideally done in transaction or with a specialized query
        // Since we don't have updateMany in BaseRepo, we do it via transaction and loop or custom query
        // Optimally: update Profile set isActive = false; update Profile set isActive = true where id = ?

        await transaction(async (txRepos) => {
            // We need a way to deactivate all. 
            // Assuming we can iterate or use a raw query if needed.
            // For now, let's fetch active ones and deactivate them
            const activeProfiles = await txRepos.profile.findActiveProfiles();
            for (const p of activeProfiles) {
                if (p.id !== id) {
                    await txRepos.profile.setActive(p.id, false);
                }
            }
            await txRepos.profile.setActive(id, true);
        });

        return this.profileRepo.findById(id) as Promise<Profile>;
    }

    async addM3USource(
        profileId: string,
        url: string,
        name?: string
    ): Promise<{ source: M3USource; jobId: string }> {
        const profile = await this.profileRepo.findById(profileId);
        if (!profile) {
            throw new AppError(404, 'Profile not found');
        }

        // Check for duplicates?
        // For now allowing duplicates as per requirements not strictly forbidding, 
        // but good practice to check. Skipping for simplicity.

        const source = await this.m3uSourceRepo.create({
            profileId,
            url,
            name: name || 'Playlist',
            lastStatus: 'IDLE',
        });

        // Trigger sync
        // We don't await the sync job here, we just trigger it (fire and forget or queue)
        // Since we don't have a queue system (Redis/Bull), we just run it async without await
        // and return a fake jobId (or the sourceId as jobId)
        this.m3uSyncJob.execute(source.id).catch(err => console.error(err));

        return { source, jobId: source.id };
    }

    async removeM3USource(profileId: string, sourceId: string): Promise<void> {
        const source = await this.m3uSourceRepo.findById(sourceId);
        if (!source || source.profileId !== profileId) {
            throw new AppError(404, 'Source not found');
        }
        await this.m3uSourceRepo.delete(sourceId);
    }

    async syncM3USource(profileId: string, sourceId: string): Promise<string> {
        const source = await this.m3uSourceRepo.findById(sourceId);
        if (!source || source.profileId !== profileId) {
            throw new AppError(404, 'Source not found');
        }

        this.m3uSyncJob.execute(source.id).catch(err => console.error(err));
        return source.id;
    }

    async getSourceStatus(profileId: string, sourceId: string): Promise<SourceSyncStatus> {
        const source = await this.m3uSourceRepo.findById(sourceId);
        if (!source || source.profileId !== profileId) {
            throw new AppError(404, 'Source not found');
        }

        return {
            status: source.lastStatus || 'IDLE',
            lastFetched: source.lastFetched,
            totalEntries: source.totalEntries,
        };
    }
}
