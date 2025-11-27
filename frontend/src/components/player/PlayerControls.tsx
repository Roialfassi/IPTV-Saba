import { Play, Pause, Volume2, VolumeX, Maximize, Minimize } from 'lucide-react';

interface PlayerControlsProps {
    isPlaying: boolean;
    volume: number;
    isMuted: boolean;
    isFullscreen: boolean;
    currentTime: number;
    duration: number;
    onPlayPause: () => void;
    onVolumeChange: (volume: number) => void;
    onMuteToggle: () => void;
    onFullscreenToggle: () => void;
    onSeek: (time: number) => void;
}

export default function PlayerControls({
    isPlaying,
    volume,
    isMuted,
    isFullscreen,
    currentTime,
    duration,
    onPlayPause,
    onVolumeChange,
    onMuteToggle,
    onFullscreenToggle,
    onSeek,
}: PlayerControlsProps) {
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4">
            {/* Progress Bar */}
            <div className="mb-3">
                <input
                    type="range"
                    min={0}
                    max={duration || 0}
                    value={currentTime}
                    onChange={(e) => onSeek(Number(e.target.value))}
                    className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                    style={{
                        background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(currentTime / duration) * 100}%, #4b5563 ${(currentTime / duration) * 100}%, #4b5563 100%)`,
                    }}
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(duration)}</span>
                </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-4">
                {/* Play/Pause */}
                <button
                    onClick={onPlayPause}
                    className="p-2 hover:bg-gray-800 rounded-full transition-colors"
                >
                    {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" fill="currentColor" />}
                </button>

                {/* Volume */}
                <div className="flex items-center gap-2">
                    <button onClick={onMuteToggle} className="p-2 hover:bg-gray-800 rounded-full">
                        {isMuted || volume === 0 ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                    </button>
                    <input
                        type="range"
                        min={0}
                        max={100}
                        value={isMuted ? 0 : volume}
                        onChange={(e) => onVolumeChange(Number(e.target.value))}
                        className="w-20 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
                    />
                </div>

                <div className="flex-1" />

                {/* Fullscreen */}
                <button
                    onClick={onFullscreenToggle}
                    className="p-2 hover:bg-gray-800 rounded-full transition-colors"
                >
                    {isFullscreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
                </button>
            </div>
        </div>
    );
}
