import { Request, Response, NextFunction } from 'express';
import { ProfileService } from '../services/ProfileService';

export class ProfileController {
    constructor(private profileService: ProfileService) { }

    getAllProfiles = async (req: Request, res: Response, next: NextFunction) => {
        const profiles = await this.profileService.getAllProfiles();
        res.status(200).json({ profiles });
    };

    getProfileById = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const profile = await this.profileService.getProfileById(profileId);
        res.status(200).json(profile);
    };

    createProfile = async (req: Request, res: Response, next: NextFunction) => {
        const profile = await this.profileService.createProfile(req.body);
        res.status(201).json(profile);
    };

    updateProfile = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const profile = await this.profileService.updateProfile(profileId, req.body);
        res.status(200).json(profile);
    };

    deleteProfile = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        await this.profileService.deleteProfile(profileId);
        res.status(200).json({ success: true, message: 'Profile deleted' });
    };

    setActiveProfile = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const profile = await this.profileService.setActiveProfile(profileId);
        res.status(200).json(profile);
    };

    addM3USource = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const { url, name } = req.body;
        const result = await this.profileService.addM3USource(profileId, url, name);
        res.status(201).json(result);
    };

    removeM3USource = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, sourceId } = req.params;
        await this.profileService.removeM3USource(profileId, sourceId);
        res.status(200).json({ success: true });
    };

    syncM3USource = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, sourceId } = req.params;
        const jobId = await this.profileService.syncM3USource(profileId, sourceId);
        res.status(200).json({ syncJobId: jobId, status: 'started' });
    };

    getSourceSyncStatus = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, sourceId } = req.params;
        const status = await this.profileService.getSourceStatus(profileId, sourceId);
        res.status(200).json(status);
    };
}
