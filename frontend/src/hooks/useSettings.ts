import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsService, UpdateSettingsData } from '../services/settings.service';
import { useProfileStore } from '../store/profileStore';

export function useSettings() {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['settings', profileId],
        queryFn: () => settingsService.getSettings(profileId!),
        enabled: !!profileId,
        staleTime: 1000 * 60 * 60, // 1 hour (settings don't change often)
    });
}

export function useUpdateSettings() {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: UpdateSettingsData) => settingsService.updateSettings(profileId!, data),
        onSuccess: (newSettings) => {
            queryClient.setQueryData(['settings', profileId], newSettings);
        },
    });
}

export function useResetSettings() {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: () => settingsService.resetSettings(profileId!),
        onSuccess: (newSettings) => {
            queryClient.setQueryData(['settings', profileId], newSettings);
        },
    });
}
