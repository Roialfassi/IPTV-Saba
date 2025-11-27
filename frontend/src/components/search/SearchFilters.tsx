import { SearchFilters as SearchFiltersType } from '../../services/search.service';

interface SearchFiltersProps {
    filters: SearchFiltersType;
    onChange: (filters: SearchFiltersType) => void;
}

export default function SearchFilters({ filters, onChange }: SearchFiltersProps) {
    const toggleContentType = (type: 'CHANNEL' | 'MOVIE' | 'SERIES') => {
        const currentTypes = filters.contentTypes || [];
        const newTypes = currentTypes.includes(type)
            ? currentTypes.filter((t) => t !== type)
            : [...currentTypes, type];

        onChange({
            ...filters,
            contentTypes: newTypes.length > 0 ? newTypes : undefined,
        });
    };

    return (
        <div className="flex flex-wrap gap-4 mb-6">
            <div className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Type:</span>
                <button
                    onClick={() => toggleContentType('CHANNEL')}
                    className={`px-3 py-1 rounded-full text-sm transition-colors ${filters.contentTypes?.includes('CHANNEL')
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                        }`}
                >
                    Channels
                </button>
                <button
                    onClick={() => toggleContentType('MOVIE')}
                    className={`px-3 py-1 rounded-full text-sm transition-colors ${filters.contentTypes?.includes('MOVIE')
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                        }`}
                >
                    Movies
                </button>
                <button
                    onClick={() => toggleContentType('SERIES')}
                    className={`px-3 py-1 rounded-full text-sm transition-colors ${filters.contentTypes?.includes('SERIES')
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                        }`}
                >
                    Series
                </button>
            </div>

            {/* Add more filters here like Year, Genre, etc. if needed */}
        </div>
    );
}
