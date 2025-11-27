import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import MovieCard from '../MovieCard';
import { usePlayerStore } from '../../../store/playerStore';
import type { Movie } from '../../../types/movie.types';

// Mock the store
vi.mock('../../../store/playerStore', () => ({
    usePlayerStore: vi.fn(),
}));

const mockMovie: Movie = {
    id: '1',
    displayName: 'Test Movie',
    url: 'http://test.com/movie.mp4',
    logo: 'http://test.com/poster.jpg',
    groupTitle: 'Action',
    contentType: 'MOVIE',
    isFavorite: false,
    profileId: 'profile1',
    parsedMetadata: {
        title: 'Test Movie',
        year: 2023,
    },
};

describe('MovieCard', () => {
    const setStreamMock = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        (usePlayerStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            setStream: setStreamMock,
        });
    });

    it('renders movie with poster', () => {
        render(<MovieCard movie={mockMovie} />);
        const img = screen.getByAltText('Test Movie');
        expect(img).toBeInTheDocument();
        expect(img).toHaveAttribute('src', mockMovie.logo);
    });

    it('renders movie without poster (shows default icon)', () => {
        const movieWithoutPoster = { ...mockMovie, logo: undefined };
        render(<MovieCard movie={movieWithoutPoster} />);
        expect(screen.queryByRole('img')).not.toBeInTheDocument();
    });

    it('calls setStream when play button clicked', () => {
        render(<MovieCard movie={mockMovie} />);
        const playButton = screen.getByLabelText('Play Test Movie');
        fireEvent.click(playButton);
        expect(setStreamMock).toHaveBeenCalledWith({
            url: mockMovie.url,
            title: mockMovie.parsedMetadata.title,
            logo: mockMovie.logo,
        });
    });

    it('displays year badge', () => {
        render(<MovieCard movie={mockMovie} />);
        expect(screen.getByText('2023')).toBeInTheDocument();
    });

    it('displays group title', () => {
        render(<MovieCard movie={mockMovie} />);
        expect(screen.getByText('Action')).toBeInTheDocument();
    });
});
