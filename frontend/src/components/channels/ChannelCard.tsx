import type { Channel } from '../../types/channel.types';
import { Play, Tv } from 'lucide-react';
import { usePlayerStore } from '../../store/playerStore';

interface ChannelCardProps {
    channel: Channel;
}

export default function ChannelCard({ channel }: ChannelCardProps) {
    const { setStream } = usePlayerStore();

    const handlePlay = () => {
        setStream({
            url: channel.url,
            title: channel.displayName,
            logo: channel.logo,
        });
    };

    return (
        <div
            onClick={handlePlay}
            className="group relative bg-gray-800 rounded-lg overflow-hidden hover:ring-2 hover:ring-primary-500 transition-all duration-200 cursor-pointer"
        >
            {/* Channel Logo/Thumbnail */}
            <div className="aspect-video bg-gray-700 flex items-center justify-center relative">
                {channel.logo ? (
                    <>
                        <img
                            src={channel.logo}
                            alt={channel.displayName}
                            className="w-full h-full object-contain p-2"
                            onError={(e) => {
                                e.currentTarget.style.display = 'none';
                                e.currentTarget.parentElement?.querySelector('.fallback-icon')?.classList.remove('hidden');
                            }}
                        />
                        <div className="fallback-icon hidden absolute inset-0 flex items-center justify-center">
                            <Tv className="w-12 h-12 text-gray-500" />
                        </div>
                    </>
                ) : (
                    <Tv className="w-12 h-12 text-gray-500" />
                )}

                {/* Play Overlay */}
                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <Play className="w-12 h-12 text-white fill-current" />
                </div>
            </div>

            {/* Channel Info */}
            <div className="p-4">
                <h3 className="font-semibold text-white truncate mb-1" title={channel.displayName}>
                    {channel.displayName}
                </h3>
                {channel.groupTitle && (
                    <p className="text-sm text-gray-400 truncate" title={channel.groupTitle}>
                        {channel.groupTitle}
                    </p>
                )}
            </div>
        </div>
    );
}
