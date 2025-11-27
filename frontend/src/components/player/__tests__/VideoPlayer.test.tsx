import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import VideoPlayer from '../VideoPlayer';
import { usePlayerStore } from '../../../store/playerStore';

// Mock video.js
vi.mock('video.js', () => ({
    default: vi.fn().mockReturnValue({
        src: vi.fn(),
        volume: vi.fn(),
        on: vi.fn(),
        dispose: vi.fn(),
    }),
}));

// Mock CSS
vi.mock('video.js/dist/video-js.css', () => ({}));

// Mock store
vi.mock('../../../store/playerStore');

describe('VideoPlayer', () => {
    const clearStreamMock = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        (usePlayerStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            currentStream: {
                url: 'http://test.com/video.m3u8',
                title: 'Test Video',
            },
            volume: 80,
            clearStream: clearStreamMock,
        });
    });

    it('renders when stream is present', () => {
        render(<VideoPlayer />);
        expect(screen.getByText('Test Video')).toBeInTheDocument();
    });

    it('does not render when no stream', () => {
        (usePlayerStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            currentStream: null,
            volume: 80,
            clearStream: clearStreamMock,
        });
        const { container } = render(<VideoPlayer />);
        expect(container).toBeEmptyDOMElement();
    });
});
