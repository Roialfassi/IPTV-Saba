import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { favoritesService } from '../services/favorites.service';
import { useProfileStore } from '../store/profileStore';

export function useFavorites(params?: { contentType?: string; page?: number; limit?: number }) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['favorites', profileId, params],
        queryFn: () => favoritesService.getFavorites(profileId!, params?.contentType, params?.page, params?.limit),
        enabled: !!profileId,
        placeholderData: (previousData) => previousData,
    });
}

export function useFavorite(contentType: 'CHANNEL' | 'MOVIE' | 'SERIES', contentId: string) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;
    const queryClient = useQueryClient();

    const { data: isFavorite, isLoading } = useQuery({
        queryKey: ['favorite', profileId, contentType, contentId],
        queryFn: () => favoritesService.checkFavorite(profileId!, contentType, contentId),
        enabled: !!profileId && !!contentId,
    });

    const addMutation = useMutation({
        mutationFn: () => favoritesService.addFavorite(profileId!, contentType, contentId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['favorite', profileId, contentType, contentId] });
            queryClient.invalidateQueries({ queryKey: ['favorites', profileId] });
            queryClient.invalidateQueries({ queryKey: ['favorites-counts', profileId] });
        },
    });

    const removeMutation = useMutation({
        mutationFn: () => favoritesService.removeFavorite(profileId!, contentType, contentId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['favorite', profileId, contentType, contentId] });
            queryClient.invalidateQueries({ queryKey: ['favorites', profileId] });
            queryClient.invalidateQueries({ queryKey: ['favorites-counts', profileId] });
        },
    });

    return {
        isFavorite,
        isLoading: isLoading || addMutation.isPending || removeMutation.isPending,
        addFavorite: addMutation.mutate,
        removeFavorite: removeMutation.mutate,
    };
}

export function useFavoriteCounts() {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['favorites-counts', profileId],
        queryFn: () => favoritesService.getCounts(profileId!),
        enabled: !!profileId,
    });
}
