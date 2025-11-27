import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ChannelCard from '../ChannelCard';
import { usePlayerStore } from '../../../store/playerStore';
import type { Channel } from '../../../types/channel.types';

// Mock the store
vi.mock('../../../store/playerStore', () => ({
    usePlayerStore: vi.fn(),
}));

const mockChannel: Channel = {
    id: '1',
    displayName: 'Test Channel',
    url: 'http://test.com/stream.m3u8',
    logo: 'http://test.com/logo.png',
    groupTitle: 'News',
    contentType: 'LIVESTREAM',
    isFavorite: false,
    profileId: 'profile1',
};

describe('ChannelCard', () => {
    const setStreamMock = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        (usePlayerStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            setStream: setStreamMock,
        });
    });

    it('renders channel with logo', () => {
        render(<ChannelCard channel={mockChannel} />);
        const img = screen.getByAltText('Test Channel');
        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute('src', mockChannel.logo);
    });

    it('renders channel without logo (shows default icon)', () => {
        const channelWithoutLogo = { ...mockChannel, logo: undefined };
        render(<ChannelCard channel={channelWithoutLogo} />);
        expect(screen.queryByRole('img')).not.toBeInTheDocument();
        // We can't easily test for the Lucide icon SVG presence without a test-id, 
        // but we can ensure no image tag is rendered.
    });

    it('calls setStream when play button clicked', () => {
        render(<ChannelCard channel={mockChannel} />);
        const playButton = screen.getByLabelText('Play Test Channel');
        fireEvent.click(playButton);
        expect(setStreamMock).toHaveBeenCalledWith({
            url: mockChannel.url,
            title: mockChannel.displayName,
            logo: mockChannel.logo,
        });
    });

    it('displays group title', () => {
        render(<ChannelCard channel={mockChannel} />);
        expect(screen.getByText('News')).toBeInTheDocument();
    });

    it('truncates long channel names', () => {
        const longNameChannel = { ...mockChannel, displayName: 'Very Long Channel Name That Should Be Truncated' };
        render(<ChannelCard channel={longNameChannel} />);
        const title = screen.getByText('Very Long Channel Name That Should Be Truncated');
        expect(title).toHaveClass('truncate');
    });
});
