import express from 'express';
import { ChannelController } from '../controllers/ChannelController';
import { ChannelService } from '../services/ChannelService';
import { repositories } from '../repositories';
import {
    getChannelsValidator,
    getChannelByIdValidator,
    searchChannelsValidator,
    validateStreamValidator,
    getGroupTitlesValidator,
} from '../validators/channel.validators';
import { validate } from '../middleware/validation.middleware';
import { asyncHandler } from '../middleware/errorHandler.middleware';

const router = express.Router();
const channelService = new ChannelService(repositories.channel, repositories.profile);
const channelController = new ChannelController(channelService);

router.get(
    '/profiles/:profileId/channels',
    getChannelsValidator,
    validate,
    asyncHandler(channelController.getChannels)
);

router.get(
    '/profiles/:profileId/channels/groups',
    getGroupTitlesValidator,
    validate,
    asyncHandler(channelController.getGroupTitles)
);

router.get(
    '/profiles/:profileId/channels/search',
    searchChannelsValidator,
    validate,
    asyncHandler(channelController.searchChannels)
);

router.get(
    '/profiles/:profileId/channels/:channelId',
    getChannelByIdValidator,
    validate,
    asyncHandler(channelController.getChannelById)
);

router.post(
    '/profiles/:profileId/channels/stream-info',
    validateStreamValidator,
    validate,
    asyncHandler(channelController.getStreamInfo)
);

export default router;
