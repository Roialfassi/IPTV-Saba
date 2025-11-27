import express from 'express';
import { ProfileController } from '../controllers/ProfileController';
import { ProfileService } from '../services/ProfileService';
import { M3USyncJob } from '../jobs/M3USyncJob';
import { repositories } from '../repositories';
import { M3UParser } from '../parsers/M3UParser';
import { ContentCategorizer } from '../categorizers/ContentCategorizer';
import {
    createProfileValidator,
    updateProfileValidator,
    profileIdValidator,
    addM3USourceValidator,
    sourceIdValidator,
} from '../validators/profile.validators';
import { validate } from '../middleware/validation.middleware';
import { asyncHandler } from '../middleware/errorHandler.middleware';

const router = express.Router();

// Dependencies
const m3uParser = new M3UParser();
// ContentCategorizer is used statically in M3USyncJob, but we pass instance as per constructor signature
const categorizer = new ContentCategorizer();

const m3uSyncJob = new M3USyncJob(
    m3uParser,
    categorizer,
    repositories.channel,
    repositories.series,
    repositories.episode,
    repositories.m3uSource
);

const profileService = new ProfileService(
    repositories.profile,
    repositories.m3uSource,
    m3uSyncJob
);

const profileController = new ProfileController(profileService);

// Profile Routes
router.get(
    '/profiles',
    asyncHandler(profileController.getAllProfiles)
);

router.post(
    '/profiles',
    createProfileValidator,
    validate,
    asyncHandler(profileController.createProfile)
);

router.get(
    '/profiles/:profileId',
    profileIdValidator,
    validate,
    asyncHandler(profileController.getProfileById)
);

router.patch(
    '/profiles/:profileId',
    updateProfileValidator,
    validate,
    asyncHandler(profileController.updateProfile)
);

router.delete(
    '/profiles/:profileId',
    profileIdValidator,
    validate,
    asyncHandler(profileController.deleteProfile)
);

router.patch(
    '/profiles/:profileId/activate',
    profileIdValidator,
    validate,
    asyncHandler(profileController.setActiveProfile)
);

// M3U Source Routes
router.post(
    '/profiles/:profileId/m3u-sources',
    addM3USourceValidator,
    validate,
    asyncHandler(profileController.addM3USource)
);

router.delete(
    '/profiles/:profileId/m3u-sources/:sourceId',
    sourceIdValidator,
    validate,
    asyncHandler(profileController.removeM3USource)
);

router.post(
    '/profiles/:profileId/m3u-sources/:sourceId/sync',
    sourceIdValidator,
    validate,
    asyncHandler(profileController.syncM3USource)
);

router.get(
    '/profiles/:profileId/m3u-sources/:sourceId/status',
    sourceIdValidator,
    validate,
    asyncHandler(profileController.getSourceSyncStatus)
);

export default router;
