import { PrismaClient, Download } from '@prisma/client';
import axios from 'axios';
import fs from 'fs/promises';
import path from 'path';
import { pipeline } from 'stream/promises';
import { createWriteStream } from 'fs';

export class DownloadService {
    private downloadDir: string;
    private activeDownloads: Map<string, AbortController> = new Map();

    constructor(
        private prisma: PrismaClient,
        downloadDir: string = './downloads'
    ) {
        this.downloadDir = downloadDir;
        this.ensureDownloadDir();
    }

    private async ensureDownloadDir() {
        try {
            await fs.mkdir(this.downloadDir, { recursive: true });
        } catch (error) {
            console.error('Failed to create download directory:', error);
        }
    }

    async queueDownload(data: {
        profileId: string;
        contentType: 'MOVIE' | 'EPISODE';
        contentId: string;
        title: string;
        logo?: string;
        url: string;
        seriesId?: string;
        seriesName?: string;
        seasonNumber?: number;
        episodeNumber?: number;
    }): Promise<Download> {
        // Check if already downloaded or in queue
        const existing = await this.prisma.download.findUnique({
            where: {
                profileId_contentType_contentId: {
                    profileId: data.profileId,
                    contentType: data.contentType,
                    contentId: data.contentId,
                },
            },
        });

        if (existing) {
            if (existing.status === 'COMPLETED') {
                throw new Error('Content already downloaded');
            }
            if (existing.status === 'DOWNLOADING') {
                throw new Error('Download already in progress');
            }
            // If failed or paused, restart
            return this.prisma.download.update({
                where: { id: existing.id },
                data: { status: 'QUEUED', error: null },
            });
        }

        // Create new download
        const download = await this.prisma.download.create({
            data: {
                ...data,
                status: 'QUEUED',
                progress: 0,
            },
        });

        // Start download asynchronously
        this.startDownload(download.id).catch(console.error);

        return download;
    }

    private async startDownload(downloadId: string) {
        const download = await this.prisma.download.findUnique({
            where: { id: downloadId },
        });

        if (!download || download.status !== 'QUEUED') {
            return;
        }

        try {
            await this.prisma.download.update({
                where: { id: downloadId },
                data: { status: 'DOWNLOADING' },
            });

            const abortController = new AbortController();
            this.activeDownloads.set(downloadId, abortController);

            // Generate file path
            const ext = this.getFileExtension(download.url);
            const fileName = `${download.contentId}${ext}`;
            const filePath = path.join(this.downloadDir, fileName);

            // Download file
            const response = await axios({
                method: 'GET',
                url: download.url,
                responseType: 'stream',
                signal: abortController.signal,
                onDownloadProgress: async (progressEvent) => {
                    const progress = progressEvent.total
                        ? (progressEvent.loaded / progressEvent.total) * 100
                        : 0;

                    await this.prisma.download.update({
                        where: { id: downloadId },
                        data: {
                            progress,
                            downloadedSize: progressEvent.loaded,
                            fileSize: progressEvent.total || 0,
                        },
                    });
                },
            });

            // Save to file
            const writeStream = createWriteStream(filePath);
            await pipeline(response.data, writeStream);

            // Mark as completed
            await this.prisma.download.update({
                where: { id: downloadId },
                data: {
                    status: 'COMPLETED',
                    progress: 100,
                    filePath,
                    completedAt: new Date(),
                },
            });

            this.activeDownloads.delete(downloadId);
        } catch (error: any) {
            console.error(`Download failed for ${downloadId}:`, error);

            await this.prisma.download.update({
                where: { id: downloadId },
                data: {
                    status: 'FAILED',
                    error: error.message,
                },
            });

            this.activeDownloads.delete(downloadId);
        }
    }

    private getFileExtension(url: string): string {
        const urlPath = new URL(url).pathname;
        const ext = path.extname(urlPath);
        return ext || '.mp4';
    }

    async pauseDownload(downloadId: string) {
        const abortController = this.activeDownloads.get(downloadId);
        if (abortController) {
            abortController.abort();
            this.activeDownloads.delete(downloadId);
        }

        await this.prisma.download.update({
            where: { id: downloadId },
            data: { status: 'PAUSED' },
        });
    }

    async resumeDownload(downloadId: string) {
        await this.prisma.download.update({
            where: { id: downloadId },
            data: { status: 'QUEUED' },
        });

        this.startDownload(downloadId).catch(console.error);
    }

    async deleteDownload(downloadId: string) {
        const download = await this.prisma.download.findUnique({
            where: { id: downloadId },
        });

        if (!download) {
            throw new Error('Download not found');
        }

        // Cancel if downloading
        this.pauseDownload(downloadId);

        // Delete file if exists
        if (download.filePath) {
            try {
                await fs.unlink(download.filePath);
            } catch (error) {
                console.error('Failed to delete file:', error);
            }
        }

        // Delete from database
        await this.prisma.download.delete({ where: { id: downloadId } });
    }

    async getDownloads(profileId: string) {
        return this.prisma.download.findMany({
            where: { profileId },
            orderBy: { createdAt: 'desc' },
        });
    }

    async getDownloadById(downloadId: string) {
        return this.prisma.download.findUnique({
            where: { id: downloadId },
        });
    }

    async getCompletedDownloads(profileId: string) {
        return this.prisma.download.findMany({
            where: {
                profileId,
                status: 'COMPLETED',
            },
            orderBy: { completedAt: 'desc' },
        });
    }
}
