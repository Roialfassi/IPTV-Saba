import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Profile } from '../types/profile.types';

interface ProfileState {
    currentProfile: Profile | null;
    profiles: Profile[];
    setCurrentProfile: (profile: Profile) => void;
    setProfiles: (profiles: Profile[]) => void;
    clearProfile: () => void;
}

export const useProfileStore = create<ProfileState>()(
    persist(
        (set) => ({
            currentProfile: null,
            profiles: [],
            setCurrentProfile: (profile) => set({ currentProfile: profile }),
            setProfiles: (profiles) => set({ profiles }),
            clearProfile: () => set({ currentProfile: null }),
        }),
        {
            name: 'iptv-profile-storage',
        }
    )
);
