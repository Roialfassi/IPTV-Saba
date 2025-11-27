import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { channelsService, type GetChannelsParams } from '../services/channels.service';
import { useProfileStore } from '../store/profileStore';

export function useChannels(params: Omit<GetChannelsParams, 'profileId'>) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['channels', currentProfile?.id, params],
        queryFn: () => channelsService.getChannels({
            profileId: currentProfile!.id,
            ...params,
        }),
        enabled: !!currentProfile,
        placeholderData: keepPreviousData,
    });
}

export function useChannelGroups() {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['channel-groups', currentProfile?.id],
        queryFn: () => channelsService.getGroupTitles(currentProfile!.id),
        enabled: !!currentProfile,
        staleTime: 10 * 60 * 1000, // 10 minutes
    });
}

export function useChannelSearch(query: string, groupTitle?: string) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['channel-search', currentProfile?.id, query, groupTitle],
        queryFn: () => channelsService.searchChannels(
            currentProfile!.id,
            query,
            groupTitle
        ),
        enabled: !!currentProfile && query.length >= 2,
    });
}
