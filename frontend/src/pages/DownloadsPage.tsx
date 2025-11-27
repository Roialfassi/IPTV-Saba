import { useDownloads } from '../hooks/useDownloads';
import { Download, Trash2, Play, Loader } from 'lucide-react';
import { usePlayerStore } from '../store/playerStore';

export default function DownloadsPage() {
    const { data: downloads, isLoading, deleteDownload } = useDownloads();
    const { setStream } = usePlayerStore();

    const handlePlay = async (download: any) => {
        // For offline playback, use the local file
        if (download.status === 'COMPLETED' && download.filePath) {
            setStream({
                url: `/api/v1/downloads/${download.id}/stream`, // Backend endpoint to stream local file
                title: download.title,
                logo: download.logo,
            });
        }
    };

    const handleDelete = async (downloadId: string) => {
        if (confirm('Delete this download?')) {
            await deleteDownload.mutateAsync(downloadId);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2 text-white">Downloads</h1>
                <p className="text-gray-400">
                    {downloads?.filter(d => d.status === 'COMPLETED').length || 0} completed downloads
                </p>
            </div>

            {/* Downloading */}
            {downloads?.filter(d => d.status === 'DOWNLOADING').length > 0 && (
                <div>
                    <h2 className="text-xl font-semibold mb-3 text-white">Downloading</h2>
                    <div className="space-y-2">
                        {downloads
                            ?.filter(d => d.status === 'DOWNLOADING')
                            .map(download => (
                                <div key={download.id} className="bg-gray-800 rounded-lg p-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <h3 className="font-semibold text-white">{download.title}</h3>
                                        <span className="text-sm text-gray-400">
                                            {Math.round(download.progress)}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-700 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full transition-all"
                                            style={{ width: `${download.progress}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                    </div>
                </div>
            )}

            {/* Completed */}
            {downloads?.filter(d => d.status === 'COMPLETED').length > 0 && (
                <div>
                    <h2 className="text-xl font-semibold mb-3 text-white">Completed</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {downloads
                            ?.filter(d => d.status === 'COMPLETED')
                            .map(download => (
                                <div key={download.id} className="bg-gray-800 rounded-lg overflow-hidden">
                                    <div className="aspect-video bg-gray-700 flex items-center justify-center">
                                        {download.logo && (
                                            <img src={download.logo} alt={download.title} className="w-full h-full object-cover" />
                                        )}
                                    </div>
                                    <div className="p-4">
                                        <h3 className="font-semibold mb-2 truncate text-white">{download.title}</h3>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handlePlay(download)}
                                                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
                                            >
                                                <Play className="w-4 h-4" />
                                                Play
                                            </button>
                                            <button
                                                onClick={() => handleDelete(download.id)}
                                                className="p-2 bg-red-600 hover:bg-red-700 rounded-lg text-white"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                    </div>
                </div>
            )}

            {downloads?.length === 0 && (
                <div className="text-center py-20">
                    <Download className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 text-lg">No downloads yet</p>
                </div>
            )}
        </div>
    );
}
