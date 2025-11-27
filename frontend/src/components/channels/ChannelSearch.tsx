import { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';

interface ChannelSearchProps {
    onSearch: (query: string) => void;
    placeholder?: string;
}

export default function ChannelSearch({ onSearch, placeholder = 'Search channels...' }: ChannelSearchProps) {
    const [query, setQuery] = useState('');

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            onSearch(query);
        }, 300);

        return () => clearTimeout(timer);
    }, [query, onSearch]);

    return (
        <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={placeholder}
                className="w-full pl-10 pr-10 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-blue-500 text-white placeholder-gray-400"
            />
            {query && (
                <button
                    onClick={() => setQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                >
                    <X className="w-5 h-5" />
                </button>
            )}
        </div>
    );
}
