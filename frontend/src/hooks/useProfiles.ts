import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { profilesService } from '../services/profiles.service';
import { useProfileStore } from '../store/profileStore';

export function useProfiles() {
    return useQuery({
        queryKey: ['profiles'],
        queryFn: () => profilesService.getAllProfiles(),
    });
}

export function useProfile(id: string, refetchInterval?: number) {
    return useQuery({
        queryKey: ['profile', id],
        queryFn: () => profilesService.getProfileById(id),
        enabled: !!id,
        refetchInterval,
    });
}

export function useCreateProfile() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: { name: string; avatar?: string }) =>
            profilesService.createProfile(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['profiles'] });
        },
    });
}

export function useUpdateProfile() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ id, data }: { id: string; data: Partial<any> }) =>
            profilesService.updateProfile(id, data),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['profiles'] });
            queryClient.invalidateQueries({ queryKey: ['profile', variables.id] });
        },
    });
}

export function useDeleteProfile() {
    const queryClient = useQueryClient();
    const { currentProfile, setCurrentProfile, profiles: storeProfiles } = useProfileStore();

    return useMutation({
        mutationFn: (id: string) => profilesService.deleteProfile(id),
        onSuccess: (_, deletedId) => {
            queryClient.invalidateQueries({ queryKey: ['profiles'] });

            // If deleted current profile, switch to another
            if (currentProfile?.id === deletedId) {
                // Note: storeProfiles might be stale, but we can try to find another one
                // Ideally, we should refetch profiles and then switch
            }
        },
    });
}

export function useSetActiveProfile() {
    const queryClient = useQueryClient();
    const { setCurrentProfile } = useProfileStore();

    return useMutation({
        mutationFn: (id: string) => profilesService.setActiveProfile(id),
        onSuccess: (profile) => {
            queryClient.invalidateQueries({ queryKey: ['profiles'] });
            setCurrentProfile(profile);
        },
    });
}

export function useAddM3USource() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ profileId, url, name }: { profileId: string; url: string; name?: string }) =>
            profilesService.addM3USource(profileId, url, name),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['profile', variables.profileId] });
            queryClient.invalidateQueries({ queryKey: ['profiles'] }); // Update stats
        },
    });
}

export function useRemoveM3USource() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ profileId, sourceId }: { profileId: string; sourceId: string }) =>
            profilesService.removeM3USource(profileId, sourceId),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['profile', variables.profileId] });
            queryClient.invalidateQueries({ queryKey: ['profiles'] }); // Update stats
        },
    });
}

export function useSyncM3USource() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ profileId, sourceId }: { profileId: string; sourceId: string }) =>
            profilesService.syncM3USource(profileId, sourceId),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['profile', variables.profileId] });
        },
    });
}
