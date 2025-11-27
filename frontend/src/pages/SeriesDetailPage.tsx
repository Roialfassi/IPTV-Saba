import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSeriesDetail, useEpisodes } from '../hooks/useSeries';
import SeasonSelector from '../components/series/SeasonSelector';
import EpisodeCard from '../components/series/EpisodeCard';
import { ArrowLeft, Loader, Tv } from 'lucide-react';

export default function SeriesDetailPage() {
    const { seriesId } = useParams<{ seriesId: string }>();
    const navigate = useNavigate();
    const [selectedSeason, setSelectedSeason] = useState<number>(1);

    const { data: series, isLoading } = useSeriesDetail(seriesId!);
    const { data: episodes, isLoading: isLoadingEpisodes } = useEpisodes(
        seriesId!,
        selectedSeason
    );

    // Set first season as selected when series loads
    useEffect(() => {
        if (series?.seasons) {
            const seasonNumbers = Object.keys(series.seasons).map(Number).sort((a, b) => a - b);
            if (seasonNumbers.length > 0) {
                setSelectedSeason(seasonNumbers[0]);
            }
        }
    }, [series]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    if (!series) {
        return (
            <div className="text-center py-20">
                <p className="text-gray-400 text-lg">Series not found</p>
            </div>
        );
    }

    const seasons = Object.keys(series.seasons)
        .map(Number)
        .sort((a, b) => a - b)
        .map(seasonNumber => ({
            seasonNumber,
            episodeCount: series.seasons[seasonNumber].length,
        }));

    return (
        <div className="space-y-6">
            {/* Back Button */}
            <button
                onClick={() => navigate('/series')}
                className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
                <ArrowLeft className="w-5 h-5" />
                Back to Series
            </button>

            {/* Series Header */}
            <div className="flex gap-6 flex-col md:flex-row">
                {/* Poster */}
                <div className="w-48 flex-shrink-0 mx-auto md:mx-0">
                    <div className="aspect-[2/3] bg-gray-700 rounded-lg overflow-hidden flex items-center justify-center">
                        {series.logo ? (
                            <img
                                src={series.logo}
                                alt={series.name}
                                className="w-full h-full object-cover"
                            />
                        ) : (
                            <Tv className="w-16 h-16 text-gray-500" />
                        )}
                    </div>
                </div>

                {/* Info */}
                <div className="flex-1 text-center md:text-left">
                    <h1 className="text-4xl font-bold mb-2">{series.name}</h1>
                    <div className="flex gap-4 text-gray-400 mb-4 justify-center md:justify-start">
                        <span>{series.totalSeasons} Season{series.totalSeasons !== 1 ? 's' : ''}</span>
                        <span>•</span>
                        <span>{series.totalEpisodes} Episodes</span>
                    </div>
                    {series.groupTitle && (
                        <p className="text-gray-400">Category: {series.groupTitle}</p>
                    )}
                </div>
            </div>

            {/* Season Selector */}
            <div>
                <h2 className="text-xl font-semibold mb-3">Seasons</h2>
                <SeasonSelector
                    seasons={seasons}
                    selectedSeason={selectedSeason}
                    onSeasonChange={setSelectedSeason}
                />
            </div>

            {/* Episodes List */}
            <div>
                <h2 className="text-xl font-semibold mb-3">
                    Season {selectedSeason} Episodes
                </h2>
                {isLoadingEpisodes ? (
                    <div className="flex items-center justify-center py-10">
                        <Loader className="w-6 h-6 animate-spin text-blue-500" />
                    </div>
                ) : episodes && episodes.length > 0 ? (
                    <div className="space-y-2">
                        {episodes.map((episode) => (
                            <EpisodeCard
                                key={episode.id}
                                episode={episode}
                                seriesName={series.name}
                                seriesLogo={series.logo}
                            />
                        ))}
                    </div>
                ) : (
                    <p className="text-gray-400 py-10 text-center">No episodes found for this season</p>
                )}
            </div>
        </div>
    );
}
