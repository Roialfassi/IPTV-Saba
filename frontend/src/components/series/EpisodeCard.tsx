import type { Episode } from '../../types/series.types';
import { Play } from 'lucide-react';
import { usePlayerStore } from '../../store/playerStore';

interface EpisodeCardProps {
    episode: Episode;
    seriesName: string;
    seriesLogo?: string;
}

export default function EpisodeCard({ episode, seriesName, seriesLogo }: EpisodeCardProps) {
    const { setStream } = usePlayerStore();

    const handlePlay = () => {
        setStream({
            url: episode.url,
            title: `${seriesName} - S${episode.seasonNumber}E${episode.episodeNumber}${episode.title ? `: ${episode.title}` : ''}`,
            logo: seriesLogo,
        });
    };

    return (
        <div className="group bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-750 transition-colors flex gap-4 p-3 items-center">
            {/* Episode Number Badge */}
            <div className="flex-shrink-0 w-16 h-16 bg-gray-700 rounded-lg flex items-center justify-center">
                <span className="text-2xl font-bold text-gray-400">
                    {episode.episodeNumber}
                </span>
            </div>

            {/* Episode Info */}
            <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-white truncate">
                    Episode {episode.episodeNumber}
                    {episode.title && `: ${episode.title}`}
                </h4>
                <p className="text-sm text-gray-400 mt-1">
                    Season {episode.seasonNumber}, Episode {episode.episodeNumber}
                </p>
            </div>

            {/* Play Button */}
            <button
                onClick={handlePlay}
                className="flex-shrink-0 w-12 h-12 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center transition-colors opacity-0 group-hover:opacity-100"
                aria-label={`Play episode ${episode.episodeNumber}`}
            >
                <Play className="w-5 h-5 fill-current text-white" />
            </button>
        </div>
    );
}
