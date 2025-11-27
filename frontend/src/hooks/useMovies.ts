import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { moviesService, type GetMoviesParams } from '../services/movies.service';
import { useProfileStore } from '../store/profileStore';

export function useMovies(params: Omit<GetMoviesParams, 'profileId'>) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['movies', currentProfile?.id, params],
        queryFn: () => moviesService.getMovies({
            profileId: currentProfile!.id,
            ...params,
        }),
        enabled: !!currentProfile,
        placeholderData: keepPreviousData,
    });
}

export function useMovieGroups() {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['movie-groups', currentProfile?.id],
        queryFn: () => moviesService.getMovieGroups(currentProfile!.id),
        enabled: !!currentProfile,
        staleTime: 10 * 60 * 1000,
    });
}

export function useMovieYears() {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['movie-years', currentProfile?.id],
        queryFn: () => moviesService.getAvailableYears(currentProfile!.id),
        enabled: !!currentProfile,
        staleTime: 10 * 60 * 1000,
    });
}

export function useMovieSearch(query: string, filters?: { year?: number; groupTitle?: string }) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['movie-search', currentProfile?.id, query, filters],
        queryFn: () => moviesService.searchMovies(
            currentProfile!.id,
            query,
            filters
        ),
        enabled: !!currentProfile && query.length >= 2,
    });
}
