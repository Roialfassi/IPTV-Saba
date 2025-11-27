import type { Profile } from '../../types/profile.types';
import { User, Check, Trash2, Edit } from 'lucide-react';

interface ProfileCardProps {
    profile: Profile;
    isActive: boolean;
    onActivate: () => void;
    onEdit: () => void;
    onDelete: () => void;
}

export default function ProfileCard({
    profile,
    isActive,
    onActivate,
    onEdit,
    onDelete,
}: ProfileCardProps) {
    return (
        <div
            className={`bg-gray-800 rounded-lg p-6 transition-all ${isActive ? 'ring-2 ring-blue-500' : 'hover:bg-gray-750'
                }`}
        >
            {/* Avatar */}
            <div className="flex items-center gap-4 mb-4">
                <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center overflow-hidden">
                    {profile.avatar ? (
                        <img
                            src={profile.avatar}
                            alt={profile.name}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <User className="w-8 h-8 text-gray-400" />
                    )}
                </div>
                <div className="flex-1">
                    <h3 className="font-semibold text-lg text-white">{profile.name}</h3>
                    {isActive && (
                        <span className="text-sm text-blue-400 flex items-center gap-1">
                            <Check className="w-4 h-4" />
                            Active Profile
                        </span>
                    )}
                </div>
            </div>

            {/* Stats */}
            {profile.stats && (
                <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
                    <div className="bg-gray-900 rounded p-2">
                        <div className="text-gray-400">Channels</div>
                        <div className="font-semibold text-white">{profile.stats.totalChannels}</div>
                    </div>
                    <div className="bg-gray-900 rounded p-2">
                        <div className="text-gray-400">Movies</div>
                        <div className="font-semibold text-white">{profile.stats.totalMovies}</div>
                    </div>
                    <div className="bg-gray-900 rounded p-2">
                        <div className="text-gray-400">Series</div>
                        <div className="font-semibold text-white">{profile.stats.totalSeries}</div>
                    </div>
                    <div className="bg-gray-900 rounded p-2">
                        <div className="text-gray-400">Sources</div>
                        <div className="font-semibold text-white">{profile.stats.m3uSourcesCount}</div>
                    </div>
                </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
                {!isActive && (
                    <button
                        onClick={onActivate}
                        className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                        Activate
                    </button>
                )}
                <button
                    onClick={onEdit}
                    className="p-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                    aria-label="Edit profile"
                >
                    <Edit className="w-5 h-5" />
                </button>
                <button
                    onClick={onDelete}
                    className="p-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                    aria-label="Delete profile"
                >
                    <Trash2 className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}
