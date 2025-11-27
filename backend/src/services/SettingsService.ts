import { PrismaClient, ProfileSettings } from '@prisma/client';

export interface UpdateSettingsData {
    // Playback
    autoplay?: boolean;
    defaultQuality?: string;
    skipIntroSeconds?: number;
    defaultVolume?: number;
    subtitlesEnabled?: boolean;
    subtitlesLanguage?: string;

    // Appearance
    theme?: string;
    accentColor?: string;
    compactMode?: boolean;
    showEPG?: boolean;
    gridSize?: string;

    // Content
    contentLanguage?: string;
    ageRating?: string;
    hideAdultContent?: boolean;

    // Data
    cacheEnabled?: boolean;
    cacheSize?: number;
    downloadQuality?: string;
    wifiOnlyDownloads?: boolean;

    // Notifications
    reminderEnabled?: boolean;
    reminderMinutes?: number;
    newContentAlert?: boolean;
}

export class SettingsService {
    constructor(private prisma: PrismaClient) { }

    async getSettings(profileId: string): Promise<ProfileSettings> {
        let settings = await this.prisma.profileSettings.findUnique({
            where: { profileId },
        });

        // Create default settings if not exists
        if (!settings) {
            settings = await this.prisma.profileSettings.create({
                data: { profileId },
            });
        }

        return settings;
    }

    async updateSettings(
        profileId: string,
        data: UpdateSettingsData
    ): Promise<ProfileSettings> {
        // Validate settings
        this.validateSettings(data);

        // Upsert settings
        return this.prisma.profileSettings.upsert({
            where: { profileId },
            update: data,
            create: {
                profileId,
                ...data,
            },
        });
    }

    private validateSettings(data: UpdateSettingsData) {
        // Validate quality settings
        const validQualities = ['auto', '1080p', '720p', '480p', '360p'];
        if (data.defaultQuality && !validQualities.includes(data.defaultQuality)) {
            throw new Error('Invalid quality setting');
        }
        if (data.downloadQuality && !validQualities.includes(data.downloadQuality)) {
            throw new Error('Invalid download quality');
        }

        // Validate volume
        if (data.defaultVolume !== undefined && (data.defaultVolume < 0 || data.defaultVolume > 100)) {
            throw new Error('Volume must be between 0 and 100');
        }

        // Validate cache size
        if (data.cacheSize !== undefined && (data.cacheSize < 0 || data.cacheSize > 10000)) {
            throw new Error('Cache size must be between 0 and 10000 MB');
        }

        // Validate theme
        const validThemes = ['dark', 'light'];
        if (data.theme && !validThemes.includes(data.theme)) {
            throw new Error('Invalid theme');
        }

        // Validate grid size
        const validGridSizes = ['small', 'medium', 'large'];
        if (data.gridSize && !validGridSizes.includes(data.gridSize)) {
            throw new Error('Invalid grid size');
        }
    }

    async resetSettings(profileId: string): Promise<ProfileSettings> {
        // Delete existing settings
        await this.prisma.profileSettings.deleteMany({
            where: { profileId },
        });

        // Create new default settings
        return this.prisma.profileSettings.create({
            data: { profileId },
        });
    }

    async exportSettings(profileId: string): Promise<any> {
        const settings = await this.getSettings(profileId);

        // Remove internal fields
        const { id, profileId: pid, createdAt, updatedAt, ...exportData } = settings;

        return {
            version: '1.0',
            settings: exportData,
            exportedAt: new Date().toISOString(),
        };
    }

    async importSettings(profileId: string, settingsData: any): Promise<ProfileSettings> {
        // Validate imported data
        if (!settingsData.settings) {
            throw new Error('Invalid settings format');
        }

        // Import settings
        return this.updateSettings(profileId, settingsData.settings);
    }
}
