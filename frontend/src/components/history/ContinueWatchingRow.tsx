import type { WatchHistory } from '../../types/history.types';
import { Play, Film, Tv } from 'lucide-react';
import { usePlayerStore } from '../../store/playerStore';

interface ContinueWatchingRowProps {
    items: WatchHistory[];
}

export default function ContinueWatchingRow({ items }: ContinueWatchingRowProps) {
    const { setStream } = usePlayerStore();

    if (items.length === 0) return null;

    const getProgressPercentage = (item: WatchHistory) => {
        if (item.duration === 0) return 0;
        return (item.progress / item.duration) * 100;
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handlePlay = (item: WatchHistory) => {
        setStream({
            url: item.url,
            title: item.title,
            logo: item.logo,
        });
    };

    return (
        <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4 text-white">Continue Watching</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {items.map((item) => (
                    <div
                        key={item.id}
                        className="group relative bg-gray-800 rounded-lg overflow-hidden hover:ring-2 hover:ring-primary-500 transition-all cursor-pointer"
                        onClick={() => handlePlay(item)}
                    >
                        {/* Thumbnail */}
                        <div className="aspect-video bg-gray-700 flex items-center justify-center relative">
                            {item.logo ? (
                                <img
                                    src={item.logo}
                                    alt={item.title}
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <div className="text-gray-500">
                                    {item.contentType === 'EPISODE' ? (
                                        <Tv className="w-12 h-12" />
                                    ) : (
                                        <Film className="w-12 h-12" />
                                    )}
                                </div>
                            )}

                            {/* Play overlay */}
                            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-60 transition-all flex items-center justify-center">
                                <Play className="w-12 h-12 transform scale-0 group-hover:scale-100 transition-transform text-white" fill="currentColor" />
                            </div>

                            {/* Progress bar */}
                            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-900">
                                <div
                                    className="h-full bg-blue-600"
                                    style={{ width: `${getProgressPercentage(item)}%` }}
                                />
                            </div>
                        </div>

                        {/* Info */}
                        <div className="p-3">
                            <h3 className="font-semibold text-sm truncate text-white">{item.title}</h3>
                            {item.contentType === 'EPISODE' && (
                                <p className="text-xs text-gray-400 mt-1">
                                    {item.seriesName} - S{item.seasonNumber}E{item.episodeNumber}
                                </p>
                            )}
                            <p className="text-xs text-gray-500 mt-1">
                                {formatTime(item.progress)} / {formatTime(item.duration)}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
