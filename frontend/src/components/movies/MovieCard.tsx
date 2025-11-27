import type { Movie } from '../../types/movie.types';
import { Play, Film, Calendar } from 'lucide-react';
import { usePlayerStore } from '../../store/playerStore';

interface MovieCardProps {
    movie: Movie;
}

export default function MovieCard({ movie }: MovieCardProps) {
    const { setStream } = usePlayerStore();

    const handlePlay = () => {
        setStream({
            url: movie.url,
            title: movie.parsedMetadata.title || movie.displayName,
            logo: movie.logo,
        });
    };

    return (
        <div
            onClick={handlePlay}
            className="group relative bg-gray-800 rounded-lg overflow-hidden hover:ring-2 hover:ring-primary-500 transition-all duration-200 cursor-pointer"
        >
            {/* Movie Poster */}
            <div className="aspect-[2/3] bg-gray-700 flex items-center justify-center relative">
                {movie.logo ? (
                    <>
                        <img
                            src={movie.logo}
                            alt={movie.parsedMetadata.title || movie.displayName}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                                e.currentTarget.style.display = 'none';
                                e.currentTarget.parentElement?.querySelector('.fallback-icon')?.classList.remove('hidden');
                            }}
                        />
                        <div className="fallback-icon hidden absolute inset-0 flex items-center justify-center">
                            <Film className="w-12 h-12 text-gray-500" />
                        </div>
                    </>
                ) : (
                    <Film className="w-12 h-12 text-gray-500" />
                )}

                {/* Year Badge */}
                {movie.parsedMetadata.year && (
                    <div className="absolute top-2 right-2 bg-black/75 px-2 py-1 rounded flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-gray-300" />
                        <span className="text-xs font-semibold text-white">{movie.parsedMetadata.year}</span>
                    </div>
                )}

                {/* Play Overlay */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <Play className="w-12 h-12 text-white fill-current" />
                </div>
            </div>

            {/* Movie Info */}
            <div className="p-4">
                <h3 className="font-semibold text-white truncate mb-1" title={movie.parsedMetadata.title || movie.displayName}>
                    {movie.parsedMetadata.title || movie.displayName}
                </h3>
                {movie.groupTitle && (
                    <p className="text-sm text-gray-400 truncate" title={movie.groupTitle}>
                        {movie.groupTitle}
                    </p>
                )}
            </div>
        </div>
    );
}
