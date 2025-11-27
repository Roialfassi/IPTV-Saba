import { create } from 'zustand';

interface PlayerState {
    isPlaying: boolean;
    currentStream: {
        url: string;
        title: string;
        logo?: string;
    } | null;
    volume: number;
    isFullscreen: boolean;
    setStream: (stream: { url: string; title: string; logo?: string }) => void;
    play: () => void;
    pause: () => void;
    setVolume: (volume: number) => void;
    toggleFullscreen: () => void;
    clearStream: () => void;
}

export const usePlayerStore = create<PlayerState>((set) => ({
    isPlaying: false,
    currentStream: null,
    volume: 80,
    isFullscreen: false,
    setStream: (stream) => set({ currentStream: stream, isPlaying: true }),
    play: () => set({ isPlaying: true }),
    pause: () => set({ isPlaying: false }),
    setVolume: (volume) => set({ volume }),
    toggleFullscreen: () => set((state) => ({ isFullscreen: !state.isFullscreen })),
    clearStream: () => set({ currentStream: null, isPlaying: false }),
}));
