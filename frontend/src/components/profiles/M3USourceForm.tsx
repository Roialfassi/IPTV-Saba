import { useState } from 'react';
import { Plus, X } from 'lucide-react';

interface M3USourceFormProps {
    onSubmit: (url: string, name?: string) => void;
    onCancel: () => void;
    isLoading?: boolean;
}

export default function M3USourceForm({ onSubmit, onCancel, isLoading }: M3USourceFormProps) {
    const [url, setUrl] = useState('');
    const [name, setName] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!url.trim()) {
            setError('URL is required');
            return;
        }

        if (!url.match(/^https?:\/\/.+/)) {
            setError('Invalid URL format');
            return;
        }

        onSubmit(url, name || undefined);
    };

    return (
        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-6 space-y-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Add M3U Source</h3>
                <button
                    type="button"
                    onClick={onCancel}
                    className="p-1 hover:bg-gray-700 rounded transition-colors text-gray-400 hover:text-white"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            <div>
                <label htmlFor="url" className="block text-sm font-medium mb-2 text-gray-300">
                    M3U URL *
                </label>
                <input
                    id="url"
                    type="text"
                    value={url}
                    onChange={(e) => {
                        setUrl(e.target.value);
                        setError('');
                    }}
                    placeholder="https://example.com/playlist.m3u"
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
                    disabled={isLoading}
                />
            </div>

            <div>
                <label htmlFor="name" className="block text-sm font-medium mb-2 text-gray-300">
                    Name (optional)
                </label>
                <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="My Playlist"
                    className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
                    disabled={isLoading}
                />
            </div>

            {error && (
                <div className="text-red-400 text-sm">{error}</div>
            )}

            <div className="flex gap-2">
                <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                    <Plus className="w-5 h-5" />
                    Add Source
                </button>
                <button
                    type="button"
                    onClick={onCancel}
                    disabled={isLoading}
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-600 text-white rounded-lg transition-colors"
                >
                    Cancel
                </button>
            </div>
        </form>
    );
}
