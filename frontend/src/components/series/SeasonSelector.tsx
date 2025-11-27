import type { SeasonInfo } from '../../types/series.types';

interface SeasonSelectorProps {
    seasons: SeasonInfo[];
    selectedSeason: number;
    onSeasonChange: (season: number) => void;
}

export default function SeasonSelector({
    seasons,
    selectedSeason,
    onSeasonChange,
}: SeasonSelectorProps) {
    return (
        <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-800">
            {seasons.map((season) => (
                <button
                    key={season.seasonNumber}
                    onClick={() => onSeasonChange(season.seasonNumber)}
                    className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${selectedSeason === season.seasonNumber
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                        }`}
                >
                    Season {season.seasonNumber}
                    <span className="ml-2 text-sm opacity-75">
                        ({season.episodeCount})
                    </span>
                </button>
            ))}
        </div>
    );
}
