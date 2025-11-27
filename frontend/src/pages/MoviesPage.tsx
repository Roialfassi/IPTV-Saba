import { useState } from 'react';
import { useMovies } from '../hooks/useMovies';
import MovieCard from '../components/movies/MovieCard';
import MovieFilters from '../components/movies/MovieFilters';
import ChannelSearch from '../components/channels/ChannelSearch';
import { ChevronLeft, ChevronRight, Loader } from 'lucide-react';

export default function MoviesPage() {
    const [page, setPage] = useState(1);
    const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
    const [selectedYear, setSelectedYear] = useState<number | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState<'name' | 'year' | 'date'>('date');
    const [order, setOrder] = useState<'asc' | 'desc'>('desc');

    const { data, isLoading, isFetching } = useMovies({
        page,
        limit: 24,
        groupTitle: selectedGroup || undefined,
        year: selectedYear || undefined,
        search: searchQuery || undefined,
        sortBy,
        order,
    });

    const totalPages = data ? Math.ceil(data.total / 24) : 0;

    const handleSortChange = (newSortBy: typeof sortBy, newOrder: typeof order) => {
        setSortBy(newSortBy);
        setOrder(newOrder);
        setPage(1);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold mb-2">Movies</h1>
                <p className="text-gray-400">
                    {data?.total || 0} movies available
                </p>
            </div>

            {/* Filters and Search */}
            <div className="flex flex-col lg:flex-row gap-4 justify-between items-start lg:items-center">
                <MovieFilters
                    selectedGroup={selectedGroup}
                    selectedYear={selectedYear}
                    sortBy={sortBy}
                    order={order}
                    onGroupChange={(group) => {
                        setSelectedGroup(group);
                        setPage(1);
                    }}
                    onYearChange={(year) => {
                        setSelectedYear(year);
                        setPage(1);
                    }}
                    onSortChange={handleSortChange}
                />
                <ChannelSearch
                    onSearch={(q) => {
                        setSearchQuery(q);
                        setPage(1);
                    }}
                    placeholder="Search movies..."
                />
            </div>

            {/* Movie Grid */}
            {isLoading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader className="w-8 h-8 animate-spin text-blue-500" />
                </div>
            ) : data?.data.length === 0 ? (
                <div className="text-center py-20">
                    <p className="text-gray-400 text-lg">No movies found</p>
                </div>
            ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                    {data?.data.map((movie) => (
                        <MovieCard key={movie.id} movie={movie} />
                    ))}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 py-8">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1 || isFetching}
                        className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <ChevronLeft className="w-5 h-5" />
                    </button>

                    <span className="text-gray-400">
                        Page {page} of {totalPages}
                    </span>

                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages || isFetching}
                        className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        <ChevronRight className="w-5 h-5" />
                    </button>
                </div>
            )}
        </div>
    );
}
