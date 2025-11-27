import type { Series } from '../../types/series.types';
import { Tv, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface SeriesCardProps {
    series: Series;
}

export default function SeriesCard({ series }: SeriesCardProps) {
    const navigate = useNavigate();

    return (
        <div
            onClick={() => navigate(`/series/${series.id}`)}
            className="group relative bg-gray-800 rounded-lg overflow-hidden hover:ring-2 hover:ring-primary-500 transition-all duration-200 cursor-pointer"
        >
            {/* Series Poster */}
            <div className="aspect-[2/3] bg-gray-700 flex items-center justify-center relative">
                {series.logo ? (
                    <>
                        <img
                            src={series.logo}
                            alt={series.name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                                e.currentTarget.style.display = 'none';
                                e.currentTarget.parentElement?.querySelector('.fallback-icon')?.classList.remove('hidden');
                            }}
                        />
                        <div className="fallback-icon hidden absolute inset-0 flex items-center justify-center">
                            <Tv className="w-12 h-12 text-gray-500" />
                        </div>
                    </>
                ) : (
                    <Tv className="w-12 h-12 text-gray-500" />
                )}

                {/* Seasons Badge */}
                <div className="absolute top-2 right-2 bg-black/75 px-2 py-1 rounded">
                    <span className="text-xs font-semibold text-white">
                        {series.totalSeasons} Season{series.totalSeasons !== 1 ? 's' : ''}
                    </span>
                </div>

                {/* Play Overlay */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <Play className="w-12 h-12 text-white fill-current" />
                </div>
            </div>

            {/* Series Info */}
            <div className="p-4">
                <h3 className="font-semibold text-white truncate mb-1" title={series.name}>
                    {series.name}
                </h3>
                <p className="text-sm text-gray-400">
                    {series.totalEpisodes} episodes
                </p>
                {series.latestEpisode && (
                    <p className="text-xs text-gray-500 mt-1">
                        Latest: S{series.latestEpisode.seasonNumber}E{series.latestEpisode.episodeNumber}
                    </p>
                )}
            </div>
        </div>
    );
}
