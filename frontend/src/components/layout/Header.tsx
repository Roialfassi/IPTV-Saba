import { useProfileStore } from '../../store/profileStore';
import { Search, Bell } from 'lucide-react';

export default function Header() {
    const { currentProfile } = useProfileStore();

    return (
        <header className="h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6">
            <div className="flex items-center bg-gray-800 rounded-full px-4 py-2 w-96">
                <Search size={18} className="text-gray-400 mr-2" />
                <input
                    type="text"
                    placeholder="Search channels, movies, series..."
                    className="bg-transparent border-none outline-none text-white placeholder-gray-400 w-full text-sm"
                />
            </div>

            <div className="flex items-center gap-4">
                <button className="text-gray-400 hover:text-white relative">
                    <Bell size={20} />
                    <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
                </button>

                <div className="flex items-center gap-3 pl-4 border-l border-gray-800">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold">
                        {currentProfile?.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="text-sm font-medium">{currentProfile?.name}</span>
                </div>
            </div>
        </header>
    );
}
