import { useState, useEffect, useRef } from 'react';
import { Search, X, Clock } from 'lucide-react';
import { useSearchSuggestions } from '../../hooks/useSearch';

interface SearchBarProps {
    onSearch: (query: string) => void;
    placeholder?: string;
}

export default function SearchBar({ onSearch, placeholder = 'Search...' }: SearchBarProps) {
    const [query, setQuery] = useState('');
    const [showSuggestions, setShowSuggestions] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const { data: suggestions } = useSearchSuggestions(query);

    useEffect(() => {
        const timer = setTimeout(() => {
            if (query.length >= 2) {
                onSearch(query);
            } else if (query.length === 0) {
                onSearch('');
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query, onSearch]);

    const handleSuggestionClick = (suggestion: string) => {
        setQuery(suggestion);
        onSearch(suggestion);
        setShowSuggestions(false);
        inputRef.current?.blur();
    };

    const handleClear = () => {
        setQuery('');
        onSearch('');
        inputRef.current?.focus();
    };

    return (
        <div className="relative">
            <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => setShowSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                    placeholder={placeholder}
                    className="w-full pl-12 pr-12 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
                />
                {query && (
                    <button
                        onClick={handleClear}
                        className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}
            </div>

            {/* Suggestions Dropdown */}
            {showSuggestions && suggestions && suggestions.length > 0 && (
                <div className="absolute top-full mt-2 w-full bg-gray-800 rounded-lg shadow-xl z-20 max-h-64 overflow-y-auto border border-gray-700">
                    {suggestions.map((suggestion, index) => (
                        <button
                            key={index}
                            onClick={() => handleSuggestionClick(suggestion)}
                            className="w-full text-left px-4 py-3 hover:bg-gray-700 transition-colors flex items-center gap-3 text-white"
                        >
                            <Clock className="w-4 h-4 text-gray-400" />
                            <span>{suggestion}</span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
