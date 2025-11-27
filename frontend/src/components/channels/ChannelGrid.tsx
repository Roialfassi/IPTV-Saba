import type { Channel } from '../../types/channel.types';
import ChannelCard from './ChannelCard';
import { Loader } from 'lucide-react';

interface ChannelGridProps {
    channels: Channel[];
    isLoading?: boolean;
}

export default function ChannelGrid({ channels, isLoading }: ChannelGridProps) {
    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    if (channels.length === 0) {
        return (
            <div className="text-center py-20">
                <p className="text-gray-400 text-lg">No channels found</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {channels.map((channel) => (
                <ChannelCard key={channel.id} channel={channel} />
            ))}
        </div>
    );
}
