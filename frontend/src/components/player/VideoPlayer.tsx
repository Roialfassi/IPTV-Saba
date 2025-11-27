import { useEffect, useRef } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';
import { usePlayerStore } from '../../store/playerStore';
import { X } from 'lucide-react';
import { useUpdateProgress } from '../../hooks/useWatchHistory';

export default function VideoPlayer() {
    const videoRef = useRef<HTMLVideoElement>(null);
    const playerRef = useRef<any>(null);
    const { currentStream, volume, clearStream } = usePlayerStore();
    const updateProgress = useUpdateProgress();

    useEffect(() => {
        if (!videoRef.current || !currentStream) return;

        // Initialize Video.js player
        const player = videojs(videoRef.current, {
            controls: true,
            autoplay: true,
            preload: 'auto',
            fluid: true,
            responsive: true,
            html5: {
                vhs: {
                    enableLowInitialPlaylist: true,
                    smoothQualityChange: true,
                    overrideNative: true,
                },
                nativeAudioTracks: false,
                nativeVideoTracks: false,
            },
            preferFullWindow: false,
        });

        playerRef.current = player;

        // Set source
        player.src({
            src: currentStream.url,
            type: currentStream.url.includes('.m3u8') ? 'application/x-mpegURL' : 'video/mp4',
        });

        // Set volume
        player.volume(volume / 100);

        // Handle errors
        player.on('error', () => {
            const error = player.error();
            console.error('Video player error:', error);
        });

        // Track progress
        const progressInterval = setInterval(() => {
            if (!player.paused()) {
                const currentTime = player.currentTime();
                const duration = player.duration();

                if (currentTime > 0 && duration > 0) {
                    // Determine content type based on stream data or URL
                    // For now, default to MOVIE if not specified
                    // Ideally, currentStream should have contentType
                    const contentType = 'MOVIE';

                    updateProgress.mutate({
                        contentType,
                        contentId: currentStream.id || currentStream.url, // Use URL as fallback ID if needed
                        title: currentStream.title,
                        logo: currentStream.logo,
                        url: currentStream.url,
                        progress: Math.floor(currentTime),
                        duration: Math.floor(duration),
                    });
                }
            }
        }, 10000); // Update every 10 seconds

        return () => {
            clearInterval(progressInterval);
            if (playerRef.current) {
                playerRef.current.dispose();
                playerRef.current = null;
            }
        };
    }, [currentStream?.url]);

    // Update volume
    useEffect(() => {
        if (playerRef.current) {
            playerRef.current.volume(volume / 100);
        }
    }, [volume]);

    if (!currentStream) {
        return null;
    }

    return (
        <div className="fixed bottom-0 right-0 z-50 w-full md:w-1/3 lg:w-1/4 bg-black shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-3 bg-gray-900">
                <div className="flex-1 min-w-0 mr-2">
                    <h3 className="text-sm font-semibold text-white truncate">
                        {currentStream.title}
                    </h3>
                </div>
                <button
                    onClick={clearStream}
                    className="p-1 hover:bg-gray-800 rounded transition-colors"
                    aria-label="Close player"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            {/* Video */}
            <div data-vjs-player>
                <video
                    ref={videoRef}
                    className="video-js vjs-big-play-centered"
                    playsInline
                />
            </div>
        </div>
    );
}
