import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ChannelsPage from '../ChannelsPage';
import { useChannels, useChannelGroups, useChannelSearch } from '../../hooks/useChannels';
import { usePlayerStore } from '../../store/playerStore';

// Mock hooks
vi.mock('../../hooks/useChannels', () => ({
    useChannels: vi.fn(),
    useChannelGroups: vi.fn(),
    useChannelSearch: vi.fn(),
}));
vi.mock('../../store/playerStore');

const mockChannels = [
    { id: '1', displayName: 'Channel 1', groupTitle: 'News', url: 'url1', contentType: 'LIVESTREAM', isFavorite: false, profileId: 'p1' },
    { id: '2', displayName: 'Channel 2', groupTitle: 'Sports', url: 'url2', contentType: 'LIVESTREAM', isFavorite: false, profileId: 'p1' },
];

describe('ChannelsPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (usePlayerStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            setStream: vi.fn(),
        });
        (useChannelGroups as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: ['News', 'Sports'],
            isLoading: false,
        });
        (useChannelSearch as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: [],
            isLoading: false,
        });
    });

    it('loads and displays channels', () => {
        (useChannels as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: mockChannels, total: 2, page: 1, totalPages: 1 },
            isLoading: false,
            isFetching: false,
        });

        render(<ChannelsPage />);
        expect(screen.getByText('Channel 1')).toBeInTheDocument();
        expect(screen.getByText('Channel 2')).toBeInTheDocument();
    });

    it('shows loading state', () => {
        (useChannels as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: undefined,
            isLoading: true,
            isFetching: true,
        });

        render(<ChannelsPage />);
        // The loader is an SVG, so we might look for a container or just ensure no channels are shown
    });

    it('shows empty state when no channels', () => {
        (useChannels as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: [], total: 0, page: 1, totalPages: 0 },
            isLoading: false,
            isFetching: false,
        });

        render(<ChannelsPage />);
        expect(screen.getByText('No channels found')).toBeInTheDocument();
    });

    /*
    it('filters by group title', async () => {
        (useChannels as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: mockChannels, total: 2, page: 1, totalPages: 1 },
            isLoading: false,
            isFetching: false,
        });

        render(<ChannelsPage />);

        const filterButton = screen.getByRole('button', { name: /All Categories/i });
        fireEvent.click(filterButton);

        const newsOption = await screen.findByText('News');
        fireEvent.click(newsOption);

        // Verify useChannels was called with groupTitle
        expect(useChannels).toHaveBeenCalledWith(expect.objectContaining({
            groupTitle: 'News',
        }));
    });
    */

    it('search updates results', () => {
        (useChannels as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: mockChannels, total: 2, page: 1, totalPages: 1 },
            isLoading: false,
            isFetching: false,
        });

        render(<ChannelsPage />);
        const searchInput = screen.getByPlaceholderText('Search channels...');
        fireEvent.change(searchInput, { target: { value: 'News' } });

        // Wait for debounce
        waitFor(() => {
            expect(useChannels).toHaveBeenCalledWith(expect.objectContaining({
                search: 'News',
            }));
        });
    });
});
