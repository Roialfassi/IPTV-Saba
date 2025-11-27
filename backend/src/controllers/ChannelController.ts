import { Request, Response, NextFunction } from 'express';
import { ChannelService } from '../services/ChannelService';

export class ChannelController {
    constructor(private channelService: ChannelService) { }

    getChannels = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const { page, limit, groupTitle, search } = req.query;

        const result = await this.channelService.getChannelsByProfile(profileId, {
            page: page ? Number(page) : 1,
            limit: limit ? Number(limit) : 50,
            groupTitle: groupTitle as string,
            search: search as string,
        });

        res.status(200).json(result);
    };

    getChannelById = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId, channelId } = req.params;
        const channel = await this.channelService.getChannelById(profileId, channelId);
        res.status(200).json(channel);
    };

    getGroupTitles = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const groups = await this.channelService.getGroupTitles(profileId);
        res.status(200).json({ groups });
    };

    searchChannels = async (req: Request, res: Response, next: NextFunction) => {
        const { profileId } = req.params;
        const { q, groupTitle } = req.query;

        const channels = await this.channelService.searchChannels(
            profileId,
            q as string,
            groupTitle as string
        );

        res.status(200).json({ channels, total: channels.length });
    };

    getStreamInfo = async (req: Request, res: Response, next: NextFunction) => {
        const { url } = req.body;
        const info = await this.channelService.validateStreamUrl(url);
        res.status(200).json(info);
    };
}
