import { useState } from 'react';
import { useFavorites } from '../hooks/useFavorites';
import { useProfileStore } from '../store/profileStore';
import ChannelCard from '../components/channels/ChannelCard';
import MovieCard from '../components/movies/MovieCard';
import SeriesCard from '../components/series/SeriesCard';
import { Heart, Loader } from 'lucide-react';

type ContentFilter = 'ALL' | 'CHANNEL' | 'MOVIE' | 'SERIES';

export default function FavoritesPage() {
    const [filter, setFilter] = useState<ContentFilter>('ALL');
    const { currentProfile } = useProfileStore();

    const { data, isLoading } = useFavorites({
        contentType: filter === 'ALL' ? undefined : filter,
    });

    const renderContent = () => {
        if (isLoading) {
            return (
                <div className="flex items-center justify-center py-20">
                    <Loader className="w-8 h-8 animate-spin text-blue-500" />
                </div>
            );
        }

        if (!data || data.favorites.length === 0) {
            return (
                <div className="text-center py-20">
                    <Heart className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 text-lg">No favorites yet</p>
                    <p className="text-gray-500 text-sm mt-2">
                        Start adding content to your favorites!
                    </p>
                </div>
            );
        }

        // Group by content type
        const channels = data.favorites.filter(f => f.contentType === 'CHANNEL');
        const movies = data.favorites.filter(f => f.contentType === 'MOVIE');
        const series = data.favorites.filter(f => f.contentType === 'SERIES');

        return (
            <div className="space-y-8">
                {(filter === 'ALL' || filter === 'CHANNEL') && channels.length > 0 && (
                    <div>
                        <h2 className="text-xl font-semibold mb-4 text-white">Channels ({channels.length})</h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                            {channels.map((fav) => (
                                <ChannelCard
                                    key={fav.id}
                                    channel={{
                                        id: fav.contentId,
                                        displayName: fav.title,
                                        logo: fav.logo,
                                        url: fav.url!,
                                        groupTitle: '',
                                    } as any}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {(filter === 'ALL' || filter === 'MOVIE') && movies.length > 0 && (
                    <div>
                        <h2 className="text-xl font-semibold mb-4 text-white">Movies ({movies.length})</h2>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                            {movies.map((fav) => (
                                <MovieCard
                                    key={fav.id}
                                    movie={{
                                        id: fav.contentId,
                                        displayName: fav.title,
                                        logo: fav.logo,
                                        url: fav.url!,
                                        parsedMetadata: { title: fav.title },
                                    } as any}
                                />
                            ))}
                        </div>
                    </div>
                )}

                {(filter === 'ALL' || filter === 'SERIES') && series.length > 0 && (
                    <div>
                        <h2 className="text-xl font-semibold mb-4 text-white">Series ({series.length})</h2>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                            {series.map((fav) => (
                                <SeriesCard
                                    key={fav.id}
                                    series={{
                                        id: fav.contentId,
                                        name: fav.title,
                                        logo: fav.logo,
                                    } as any}
                                />
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-2 text-white">My Favorites</h1>
                <p className="text-gray-400">
                    {data?.total || 0} items in your favorites
                </p>
            </div>

            {/* Filter Tabs */}
            <div className="flex gap-2 border-b border-gray-800">
                {(['ALL', 'CHANNEL', 'MOVIE', 'SERIES'] as ContentFilter[]).map((type) => (
                    <button
                        key={type}
                        onClick={() => setFilter(type)}
                        className={`px-4 py-2 font-medium transition-colors ${filter === type
                                ? 'text-blue-500 border-b-2 border-blue-500'
                                : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        {type === 'ALL' ? 'All' : type === 'CHANNEL' ? 'Channels' : type === 'MOVIE' ? 'Movies' : 'Series'}
                    </button>
                ))}
            </div>

            {renderContent()}
        </div>
    );
}
