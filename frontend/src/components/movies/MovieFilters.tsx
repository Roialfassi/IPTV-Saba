import { useState } from 'react';
import { X, Calendar, Grid } from 'lucide-react';
import { useMovieGroups, useMovieYears } from '../../hooks/useMovies';

interface MovieFiltersProps {
    selectedGroup: string | null;
    selectedYear: number | null;
    sortBy: 'name' | 'year' | 'date';
    order: 'asc' | 'desc';
    onGroupChange: (group: string | null) => void;
    onYearChange: (year: number | null) => void;
    onSortChange: (sortBy: 'name' | 'year' | 'date', order: 'asc' | 'desc') => void;
}

export default function MovieFilters({
    selectedGroup,
    selectedYear,
    sortBy,
    order,
    onGroupChange,
    onYearChange,
    onSortChange,
}: MovieFiltersProps) {
    const [isGroupOpen, setIsGroupOpen] = useState(false);
    const [isYearOpen, setIsYearOpen] = useState(false);
    const { data: groups } = useMovieGroups();
    const { data: years } = useMovieYears();

    return (
        <div className="flex flex-wrap gap-3">
            {/* Category Filter */}
            <div className="relative">
                <button
                    onClick={() => setIsGroupOpen(!isGroupOpen)}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors border border-gray-700"
                >
                    <Grid className="w-4 h-4" />
                    <span className="hidden sm:inline max-w-[150px] truncate">{selectedGroup || 'All Categories'}</span>
                    <span className="sm:hidden">Categories</span>
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

                {isGroupOpen && (
                    <>
                        <div className="fixed inset-0 z-10" onClick={() => setIsGroupOpen(false)} />
                        <div className="absolute top-full mt-2 left-0 bg-gray-800 rounded-lg shadow-xl z-20 max-h-96 overflow-y-auto w-64 border border-gray-700">
                            <button
                                onClick={() => {
                                    onGroupChange(null);
                                    setIsGroupOpen(false);
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
                                        setIsGroupOpen(false);
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

            {/* Year Filter */}
            <div className="relative">
                <button
                    onClick={() => setIsYearOpen(!isYearOpen)}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors border border-gray-700"
                >
                    <Calendar className="w-4 h-4" />
                    <span className="hidden sm:inline">{selectedYear || 'All Years'}</span>
                    <span className="sm:hidden">Years</span>
                    {selectedYear && (
                        <X
                            className="w-4 h-4 ml-2 hover:text-red-400"
                            onClick={(e) => {
                                e.stopPropagation();
                                onYearChange(null);
                            }}
                        />
                    )}
                </button>

                {isYearOpen && (
                    <>
                        <div className="fixed inset-0 z-10" onClick={() => setIsYearOpen(false)} />
                        <div className="absolute top-full mt-2 left-0 bg-gray-800 rounded-lg shadow-xl z-20 max-h-96 overflow-y-auto w-48 border border-gray-700">
                            <button
                                onClick={() => {
                                    onYearChange(null);
                                    setIsYearOpen(false);
                                }}
                                className="w-full text-left px-4 py-3 hover:bg-gray-700 transition-colors border-b border-gray-700"
                            >
                                All Years
                            </button>
                            {years?.map((year) => (
                                <button
                                    key={year}
                                    onClick={() => {
                                        onYearChange(year);
                                        setIsYearOpen(false);
                                    }}
                                    className={`w-full text-left px-4 py-3 hover:bg-gray-700 transition-colors ${selectedYear === year ? 'bg-gray-700 text-blue-400' : ''
                                        }`}
                                >
                                    {year}
                                </button>
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* Sort Options */}
            <select
                value={`${sortBy}-${order}`}
                onChange={(e) => {
                    const [newSortBy, newOrder] = e.target.value.split('-') as [typeof sortBy, typeof order];
                    onSortChange(newSortBy, newOrder);
                }}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors border border-gray-700 focus:ring-2 focus:ring-blue-500 cursor-pointer text-white"
            >
                <option value="name-asc">Title A-Z</option>
                <option value="name-desc">Title Z-A</option>
                <option value="year-desc">Newest First</option>
                <option value="year-asc">Oldest First</option>
                <option value="date-desc">Recently Added</option>
            </select>
        </div>
    );
}
