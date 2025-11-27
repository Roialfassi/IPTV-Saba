import { useState } from 'react';
import { useSeries } from '../hooks/useSeries';
import SeriesCard from '../components/series/SeriesCard';
import ChannelSearch from '../components/channels/ChannelSearch';
import { ChevronLeft, ChevronRight, Loader } from 'lucide-react';

export default function SeriesPage() {
    const [page, setPage] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');

    const { data, isLoading, isFetching } = useSeries({
        page,
        limit: 24,
        search: searchQuery || undefined,
    });

    const totalPages = data ? Math.ceil(data.total / 24) : 0;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold mb-2">TV Series</h1>
                <p className="text-gray-400">
                    {data?.total || 0} series available
                </p>
            </div>

            {/* Search */}
            <div className="max-w-md">
                <ChannelSearch
                    onSearch={(q) => {
                        setSearchQuery(q);
                        setPage(1);
                    }}
                    placeholder="Search series..."
                />
            </div>

            {/* Series Grid */}
            {isLoading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader className="w-8 h-8 animate-spin text-blue-500" />
                </div>
            ) : data?.data.length === 0 ? (
                <div className="text-center py-20">
                    <p className="text-gray-400 text-lg">No series found</p>
                </div>
            ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                    {data?.data.map((series) => (
                        <SeriesCard key={series.id} series={series} />
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
