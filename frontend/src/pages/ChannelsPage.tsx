import { useState } from 'react';
import { useChannels } from '../hooks/useChannels';
import ChannelGrid from '../components/channels/ChannelGrid';
import ChannelFilters from '../components/channels/ChannelFilters';
import ChannelSearch from '../components/channels/ChannelSearch';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function ChannelsPage() {
    const [page, setPage] = useState(1);
    const [selectedGroup, setSelectedGroup] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');

    const { data, isLoading, isFetching } = useChannels({
        page,
        limit: 20,
        groupTitle: selectedGroup || undefined,
        search: searchQuery || undefined,
    });

    const totalPages = data ? Math.ceil(data.total / 20) : 0;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold mb-2">Live Channels</h1>
                <p className="text-gray-400">
                    {data?.total || 0} channels available
                </p>
            </div>

            {/* Filters and Search */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <ChannelFilters
                    selectedGroup={selectedGroup}
                    onGroupChange={(group) => {
                        setSelectedGroup(group);
                        setPage(1);
                    }}
                />
                <ChannelSearch onSearch={(query) => {
                    setSearchQuery(query);
                    setPage(1);
                }} />
            </div>

            {/* Channel Grid */}
            <ChannelGrid
                channels={data?.data || []} // Note: data.data because PaginatedResponse has data property
                isLoading={isLoading}
            />

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
