import { useState } from 'react';
import { X } from 'lucide-react';

interface CreateProfileModalProps {
    onSubmit: (name: string) => void;
    onCancel: () => void;
    isLoading?: boolean;
}

export default function CreateProfileModal({ onSubmit, onCancel, isLoading }: CreateProfileModalProps) {
    const [name, setName] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!name.trim()) {
            setError('Profile name is required');
            return;
        }

        onSubmit(name.trim());
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-lg w-full max-w-md overflow-hidden shadow-xl">
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xl font-bold text-white">Create Profile</h3>
                        <button
                            type="button"
                            onClick={onCancel}
                            className="p-1 hover:bg-gray-700 rounded transition-colors text-gray-400 hover:text-white"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    <div>
                        <label htmlFor="profileName" className="block text-sm font-medium mb-2 text-gray-300">
                            Profile Name
                        </label>
                        <input
                            id="profileName"
                            type="text"
                            value={name}
                            onChange={(e) => {
                                setName(e.target.value);
                                setError('');
                            }}
                            placeholder="e.g. Kids, Living Room"
                            className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
                            disabled={isLoading}
                            autoFocus
                        />
                        {error && (
                            <p className="text-red-400 text-sm mt-1">{error}</p>
                        )}
                    </div>

                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onCancel}
                            disabled={isLoading}
                            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-600 text-white rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                        >
                            {isLoading ? 'Creating...' : 'Create Profile'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
