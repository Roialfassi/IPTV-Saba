import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ProfilesPage from '../ProfilesPage';
import { useProfiles, useCreateProfile, useSetActiveProfile, useDeleteProfile, useAddM3USource, useRemoveM3USource, useSyncM3USource } from '../../hooks/useProfiles';
import { useProfileStore } from '../../store/profileStore';

// Mock hooks
vi.mock('../../hooks/useProfiles', () => ({
    useProfiles: vi.fn(),
    useCreateProfile: vi.fn(),
    useSetActiveProfile: vi.fn(),
    useDeleteProfile: vi.fn(),
    useAddM3USource: vi.fn(),
    useRemoveM3USource: vi.fn(),
    useSyncM3USource: vi.fn(),
}));
vi.mock('../../store/profileStore');

const mockProfiles = [
    { id: '1', name: 'Profile 1', isActive: true, m3uSources: [] },
    { id: '2', name: 'Profile 2', isActive: false, m3uSources: [] },
];

describe('ProfilesPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (useProfileStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            currentProfile: mockProfiles[0],
        });
        (useCreateProfile as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ mutateAsync: vi.fn() });
        (useSetActiveProfile as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ mutate: vi.fn() });
        (useDeleteProfile as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ mutate: vi.fn() });
        (useAddM3USource as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
        (useRemoveM3USource as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ mutate: vi.fn() });
        (useSyncM3USource as unknown as ReturnType<typeof vi.fn>).mockReturnValue({ mutate: vi.fn(), isPending: false });
    });

    it('loads and displays profiles', () => {
        (useProfiles as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: mockProfiles,
            isLoading: false,
        });

        render(<ProfilesPage />);
        expect(screen.getByText('Profile 1')).toBeInTheDocument();
        expect(screen.getByText('Profile 2')).toBeInTheDocument();
    });

    it('shows loading state', () => {
        (useProfiles as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: undefined,
            isLoading: true,
        });

        render(<ProfilesPage />);
        // Check for loader (implementation detail)
        expect(screen.queryByText('Profile 1')).not.toBeInTheDocument();
    });

    it('opens add source form', () => {
        (useProfiles as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: mockProfiles,
            isLoading: false,
        });

        render(<ProfilesPage />);

        // Find the "Add Source" button in the M3U Sources section
        // The top one is "Create Profile", the M3U one is "Add Source"
        const addSourceButton = screen.getByRole('button', { name: /Add Source/i });
        fireEvent.click(addSourceButton);

        expect(screen.getByLabelText('M3U URL *')).toBeInTheDocument();
    });
});
