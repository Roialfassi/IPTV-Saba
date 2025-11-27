import { useState, useEffect, useCallback } from 'react';

export function useVideoPlayer(videoElement: HTMLVideoElement | null) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(80);
    const [isMuted, setIsMuted] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        if (!videoElement) return;

        const handlePlay = () => setIsPlaying(true);
        const handlePause = () => setIsPlaying(false);
        const handleTimeUpdate = () => setCurrentTime(videoElement.currentTime);
        const handleDurationChange = () => setDuration(videoElement.duration);
        const handleVolumeChange = () => {
            setVolume(videoElement.volume * 100);
            setIsMuted(videoElement.muted);
        };

        videoElement.addEventListener('play', handlePlay);
        videoElement.addEventListener('pause', handlePause);
        videoElement.addEventListener('timeupdate', handleTimeUpdate);
        videoElement.addEventListener('durationchange', handleDurationChange);
        videoElement.addEventListener('volumechange', handleVolumeChange);

        return () => {
            videoElement.removeEventListener('play', handlePlay);
            videoElement.removeEventListener('pause', handlePause);
            videoElement.removeEventListener('timeupdate', handleTimeUpdate);
            videoElement.removeEventListener('durationchange', handleDurationChange);
            videoElement.removeEventListener('volumechange', handleVolumeChange);
        };
    }, [videoElement]);

    const play = useCallback(() => {
        videoElement?.play();
    }, [videoElement]);

    const pause = useCallback(() => {
        videoElement?.pause();
    }, [videoElement]);

    const togglePlayPause = useCallback(() => {
        if (isPlaying) {
            pause();
        } else {
            play();
        }
    }, [isPlaying, play, pause]);

    const seek = useCallback((time: number) => {
        if (videoElement) {
            videoElement.currentTime = time;
        }
    }, [videoElement]);

    const changeVolume = useCallback((newVolume: number) => {
        if (videoElement) {
            videoElement.volume = newVolume / 100;
            setVolume(newVolume);
        }
    }, [videoElement]);

    const toggleMute = useCallback(() => {
        if (videoElement) {
            videoElement.muted = !videoElement.muted;
        }
    }, [videoElement]);

    const toggleFullscreen = useCallback(() => {
        if (!document.fullscreenElement) {
            videoElement?.requestFullscreen();
            setIsFullscreen(true);
        } else {
            document.exitFullscreen();
            setIsFullscreen(false);
        }
    }, [videoElement]);

    return {
        isPlaying,
        currentTime,
        duration,
        volume,
        isMuted,
        isFullscreen,
        play,
        pause,
        togglePlayPause,
        seek,
        changeVolume,
        toggleMute,
        toggleFullscreen,
    };
}
