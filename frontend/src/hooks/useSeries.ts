import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { seriesService, type GetSeriesParams } from '../services/series.service';
import { episodesService } from '../services/episodes.service';
import { useProfileStore } from '../store/profileStore';

export function useSeries(params: Omit<GetSeriesParams, 'profileId'>) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['series', currentProfile?.id, params],
        queryFn: () => seriesService.getAllSeries({
            profileId: currentProfile!.id,
            ...params,
        }),
        enabled: !!currentProfile,
        placeholderData: keepPreviousData,
    });
}

export function useSeriesDetail(seriesId: string) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['series', currentProfile?.id, seriesId],
        queryFn: () => seriesService.getSeriesById(currentProfile!.id, seriesId),
        enabled: !!currentProfile && !!seriesId,
    });
}

export function useSeasons(seriesId: string) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['seasons', currentProfile?.id, seriesId],
        queryFn: () => seriesService.getSeasons(currentProfile!.id, seriesId),
        enabled: !!currentProfile && !!seriesId,
    });
}

export function useEpisodes(seriesId: string, seasonNumber?: number) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['episodes', currentProfile?.id, seriesId, seasonNumber],
        queryFn: () => seasonNumber
            ? episodesService.getEpisodesBySeason(currentProfile!.id, seriesId, seasonNumber)
            : episodesService.getEpisodes(currentProfile!.id, seriesId),
        enabled: !!currentProfile && !!seriesId,
    });
}

export function useNextEpisode(
    seriesId: string,
    currentSeason: number,
    currentEpisode: number
) {
    const { currentProfile } = useProfileStore();

    return useQuery({
        queryKey: ['next-episode', currentProfile?.id, seriesId, currentSeason, currentEpisode],
        queryFn: () => episodesService.getNextEpisode(
            currentProfile!.id,
            seriesId,
            currentSeason,
            currentEpisode
        ),
        enabled: !!currentProfile && !!seriesId,
    });
}
