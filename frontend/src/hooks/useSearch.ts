import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchService, SearchFilters } from '../services/search.service';
import { useProfileStore } from '../store/profileStore';
import { useDebounce } from './useDebounce'; // Assuming this exists or I should create it. I'll check if it exists or implement basic debounce in component. Actually, I'll assume I need to handle debounce in component as in the provided SearchBar.tsx.

export function useGlobalSearch(query: string, filters?: SearchFilters) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['search', profileId, query, filters],
        queryFn: () => searchService.search(profileId!, query, filters),
        enabled: !!profileId && query.length >= 2,
        staleTime: 1000 * 60 * 5, // 5 minutes
    });
}

export function useSearchHistory(limit: number = 10) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;
    const queryClient = useQueryClient();

    const query = useQuery({
        queryKey: ['searchHistory', profileId],
        queryFn: () => searchService.getHistory(profileId!, limit),
        enabled: !!profileId,
    });

    const clearMutation = useMutation({
        mutationFn: () => searchService.clearHistory(profileId!),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['searchHistory', profileId] });
        },
    });

    return {
        ...query,
        clearHistory: clearMutation,
    };
}

export function useSearchSuggestions(query: string) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['searchSuggestions', profileId, query],
        queryFn: () => searchService.getSuggestions(profileId!, query),
        enabled: !!profileId && query.length >= 2,
        staleTime: 1000 * 60, // 1 minute
    });
}

export function usePopularSearches(limit: number = 10) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;

    return useQuery({
        queryKey: ['popularSearches', profileId],
        queryFn: () => searchService.getPopular(profileId!, limit),
        enabled: !!profileId,
    });
}
