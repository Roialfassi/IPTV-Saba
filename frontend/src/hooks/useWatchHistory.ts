import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { historyService } from '../services/history.service';
import type { UpdateProgressData } from '../types/history.types';
import { useProfileStore } from '../store/profileStore';

export function useWatchHistory(page: number = 1, limit: number = 20) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['history', profileId, page, limit],
        queryFn: () => historyService.getHistory(profileId!, page, limit),
        enabled: !!profileId,
    });
}

export function useContinueWatching(limit: number = 10) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['continue-watching', profileId, limit],
        queryFn: () => historyService.getContinueWatching(profileId!, limit),
        enabled: !!profileId,
    });
}

export function useUpdateProgress() {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: UpdateProgressData) =>
            historyService.updateProgress(profileId!, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['continue-watching', profileId] });
            queryClient.invalidateQueries({ queryKey: ['history', profileId] });
        },
    });
}

export function useContentProgress(contentType: string, contentId: string) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['progress', profileId, contentType, contentId],
        queryFn: () => historyService.getProgress(profileId!, contentType, contentId),
        enabled: !!profileId && !!contentId,
    });
}
