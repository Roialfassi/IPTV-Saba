import { useState } from 'react';
import { Filter, X } from 'lucide-react';
import { useChannelGroups } from '../../hooks/useChannels';

interface ChannelFiltersProps {
    selectedGroup: string | null;
    onGroupChange: (group: string | null) => void;
}

export default function ChannelFilters({ selectedGroup, onGroupChange }: ChannelFiltersProps) {
    const { data: groups, isLoading } = useChannelGroups();
    const [isOpen, setIsOpen] = useState(false);

    if (isLoading) {
        return <div className="animate-pulse bg-gray-800 h-10 w-32 rounded"></div>;
    }

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors border border-gray-700"
            >
                <Filter className="w-4 h-4" />
                <span className="max-w-[150px] truncate">{selectedGroup || 'All Categories'}</span>
                {selectedGroup && (
                    <X
                        className="w-4 h-4 ml-2 hover:text-red-400"
                        onClick={(e) => {
                            e.stopPropagation();
                            onGroupChange(null);
                        }}
                    />
                )}
            </button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Dropdown */}
                    <div className="absolute top-full mt-2 left-0 bg-gray-800 rounded-lg shadow-xl z-20 max-h-96 overflow-y-auto w-64 border border-gray-700">
                        <button
                            onClick={() => {
                                onGroupChange(null);
                                setIsOpen(false);
                            }}
                            className="w-full text-left px-4 py-3 hover:bg-gray-700 transition-colors border-b border-gray-700"
                        >
                            All Categories
                        </button>
                        {groups?.map((group) => (
                            <button
                                key={group}
                                onClick={() => {
                                    onGroupChange(group);
                                    setIsOpen(false);
                                }}
                                className={`w-full text-left px-4 py-3 hover:bg-gray-700 transition-colors ${selectedGroup === group ? 'bg-gray-700 text-blue-400' : ''
                                    }`}
                            >
                                {group}
                            </button>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
