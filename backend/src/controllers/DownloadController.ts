import { Request, Response, NextFunction } from 'express';
import { DownloadService } from '../services/DownloadService';
import path from 'path';
import fs from 'fs';

export class DownloadController {
    constructor(private downloadService: DownloadService) { }

    // GET /api/v1/profiles/:profileId/downloads
    async getDownloads(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const downloads = await this.downloadService.getDownloads(profileId);
            res.json(downloads);
        } catch (error) {
            next(error);
        }
    }

    // POST /api/v1/profiles/:profileId/downloads
    async queueDownload(req: Request, res: Response, next: NextFunction) {
        try {
            const { profileId } = req.params;
            const data = req.body;
            const download = await this.downloadService.queueDownload({
                profileId,
                ...data,
            });
            res.json(download);
        } catch (error) {
            next(error);
        }
    }

    // POST /api/v1/downloads/:downloadId/pause
    async pauseDownload(req: Request, res: Response, next: NextFunction) {
        try {
            const { downloadId } = req.params;
            await this.downloadService.pauseDownload(downloadId);
            res.json({ success: true });
        } catch (error) {
            next(error);
        }
    }

    // POST /api/v1/downloads/:downloadId/resume
    async resumeDownload(req: Request, res: Response, next: NextFunction) {
        try {
            const { downloadId } = req.params;
            await this.downloadService.resumeDownload(downloadId);
            res.json({ success: true });
        } catch (error) {
            next(error);
        }
    }

    // DELETE /api/v1/downloads/:downloadId
    async deleteDownload(req: Request, res: Response, next: NextFunction) {
        try {
            const { downloadId } = req.params;
            await this.downloadService.deleteDownload(downloadId);
            res.json({ success: true });
        } catch (error) {
            next(error);
        }
    }

    // GET /api/v1/downloads/:downloadId/stream
    async streamDownload(req: Request, res: Response, next: NextFunction) {
        try {
            const { downloadId } = req.params;
            const download = await this.downloadService.getDownloadById(downloadId);

            if (!download || !download.filePath) {
                res.status(404).json({ error: 'Download not found or file missing' });
                return;
            }

            const filePath = path.resolve(download.filePath);

            if (!fs.existsSync(filePath)) {
                res.status(404).json({ error: 'File not found on server' });
                return;
            }

            res.sendFile(filePath);
        } catch (error) {
            next(error);
        }
    }
}
