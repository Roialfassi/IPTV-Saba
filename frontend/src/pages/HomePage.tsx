import { useContinueWatching } from '../hooks/useWatchHistory';
import ContinueWatchingRow from '../components/history/ContinueWatchingRow';
import { Loader } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useProfileStore } from '../store/profileStore';

export default function HomePage() {
    const { data: continueWatching, isLoading } = useContinueWatching();
    const { currentProfile } = useProfileStore();

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold mb-2 text-white">Welcome Back, {currentProfile?.name}!</h1>
                <p className="text-gray-400">Pick up where you left off</p>
            </div>

            {isLoading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader className="w-8 h-8 animate-spin text-blue-500" />
                </div>
            ) : (
                continueWatching && continueWatching.length > 0 && <ContinueWatchingRow items={continueWatching} />
            )}

            {/* Quick Links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <QuickLinkCard
                    title="Live Channels"
                    description="Watch live TV"
                    href="/channels"
                    icon="📺"
                />
                <QuickLinkCard
                    title="Movies"
                    description="Browse movies"
                    href="/movies"
                    icon="🎬"
                />
                <QuickLinkCard
                    title="Series"
                    description="Watch TV shows"
                    href="/series"
                    icon="📺"
                />
            </div>
        </div>
    );
}

function QuickLinkCard({ title, description, href, icon }: any) {
    return (
        <Link
            to={href}
            className="block bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors hover:ring-2 hover:ring-blue-500"
        >
            <div className="text-4xl mb-3">{icon}</div>
            <h3 className="text-xl font-semibold mb-1 text-white">{title}</h3>
            <p className="text-gray-400 text-sm">{description}</p>
        </Link>
    );
}
