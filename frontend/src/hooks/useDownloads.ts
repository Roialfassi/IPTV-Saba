import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { downloadsService, Download } from '../services/downloads.service';
import { useProfileStore } from '../store/profileStore';

export function useDownloads() {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;
    const queryClient = useQueryClient();

    const query = useQuery({
        queryKey: ['downloads', profileId],
        queryFn: () => downloadsService.getDownloads(profileId!),
        enabled: !!profileId,
        // Poll every 2 seconds for progress updates when there are active downloads
        refetchInterval: (query) => {
            const hasActiveDownloads = query.state.data?.some(
                (d) => d.status === 'DOWNLOADING' || d.status === 'QUEUED'
            );
            return hasActiveDownloads ? 2000 : false;
        },
    });

    const deleteMutation = useMutation({
        mutationFn: downloadsService.deleteDownload,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['downloads', profileId] });
        },
    });

    return {
        ...query,
        deleteDownload: deleteMutation,
    };
}

export function useDownload(contentType: string, contentId: string) {
    const { currentProfile } = useProfileStore();
    const profileId = currentProfile?.id;
    const queryClient = useQueryClient();

    // Find download in the list
    const { data: downloads } = useQuery({
        queryKey: ['downloads', profileId],
        queryFn: () => downloadsService.getDownloads(profileId!),
        enabled: !!profileId,
    });

    const download = downloads?.find(
        (d) => d.contentType === contentType && d.contentId === contentId
    );

    const queueMutation = useMutation({
        mutationFn: (data: any) =>
            downloadsService.queueDownload({ ...data, profileId: profileId! }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['downloads', profileId] });
        },
    });

    const pauseMutation = useMutation({
        mutationFn: downloadsService.pauseDownload,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['downloads', profileId] });
        },
    });

    const resumeMutation = useMutation({
        mutationFn: downloadsService.resumeDownload,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['downloads', profileId] });
        },
    });

    return {
        download,
        isDownloaded: download?.status === 'COMPLETED',
        isDownloading: download?.status === 'DOWNLOADING' || download?.status === 'QUEUED',
        progress: download?.progress || 0,
        queueDownload: queueMutation.mutateAsync,
        pauseDownload: pauseMutation.mutateAsync,
        resumeDownload: resumeMutation.mutateAsync,
    };
}
