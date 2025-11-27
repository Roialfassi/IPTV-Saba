import { useState } from 'react';
import { useGlobalSearch, useSearchHistory } from '../hooks/useSearch';
import SearchBar from '../components/search/SearchBar';
import SearchFilters from '../components/search/SearchFilters';
import ChannelCard from '../components/channels/ChannelCard';
import MovieCard from '../components/movies/MovieCard';
import SeriesCard from '../components/series/SeriesCard';
import { Search as SearchIcon, Loader, Trash2 } from 'lucide-react';

export default function SearchPage() {
    const [query, setQuery] = useState('');
    const [filters, setFilters] = useState({});

    const { data: results, isLoading } = useGlobalSearch(query, filters);
    const { data: history, clearHistory } = useSearchHistory();

    const hasResults = results && (
        results.channels.length > 0 ||
        results.movies.length > 0 ||
        results.series.length > 0
    );

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold mb-4 text-white">Search</h1>
                <SearchBar
                    onSearch={setQuery}
                    placeholder="Search for channels, movies, or series..."
                />
            </div>

            {/* Search Filters */}
            <SearchFilters filters={filters} onChange={setFilters} />

            {/* Search History */}
            {!query && history && history.length > 0 && (
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-xl font-semibold text-white">Recent Searches</h2>
                        <button
                            onClick={() => clearHistory.mutate()}
                            className="text-sm text-red-400 hover:text-red-300 flex items-center gap-1"
                        >
                            <Trash2 className="w-4 h-4" />
                            Clear History
                        </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {history.map((item, index) => (
                            <button
                                key={index}
                                onClick={() => setQuery(item.query)}
                                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors text-gray-300 hover:text-white"
                            >
                                {item.query}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Results */}
            {isLoading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader className="w-8 h-8 animate-spin text-blue-500" />
                </div>
            ) : query && !hasResults ? (
                <div className="text-center py-20">
                    <SearchIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400 text-lg">No results found for "{query}"</p>
                    <p className="text-gray-500 text-sm mt-2">
                        Try different keywords or adjust your filters
                    </p>
                </div>
            ) : hasResults && results ? (
                <div className="space-y-8">
                    {/* Channels */}
                    {results.channels.length > 0 && (
                        <div>
                            <h2 className="text-xl font-semibold mb-4 text-white">
                                Channels ({results.channels.length})
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                                {results.channels.map((channel: any) => (
                                    <ChannelCard key={channel.id} channel={channel} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Movies */}
                    {results.movies.length > 0 && (
                        <div>
                            <h2 className="text-xl font-semibold mb-4 text-white">
                                Movies ({results.movies.length})
                            </h2>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                                {results.movies.map((movie: any) => (
                                    <MovieCard key={movie.id} movie={movie} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Series */}
                    {results.series.length > 0 && (
                        <div>
                            <h2 className="text-xl font-semibold mb-4 text-white">
                                Series ({results.series.length})
                            </h2>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                                {results.series.map((series: any) => (
                                    <SeriesCard key={series.id} series={series} />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            ) : null}
        </div>
    );
}
