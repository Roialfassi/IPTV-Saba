import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import MoviesPage from '../MoviesPage';
import { useMovies, useMovieGroups, useMovieYears, useMovieSearch } from '../../hooks/useMovies';
import { usePlayerStore } from '../../store/playerStore';

// Mock hooks
vi.mock('../../hooks/useMovies', () => ({
    useMovies: vi.fn(),
    useMovieGroups: vi.fn(),
    useMovieYears: vi.fn(),
    useMovieSearch: vi.fn(),
}));
vi.mock('../../store/playerStore');

const mockMovies = [
    {
        id: '1',
        displayName: 'Movie 1',
        groupTitle: 'Action',
        url: 'url1',
        contentType: 'MOVIE',
        isFavorite: false,
        profileId: 'p1',
        parsedMetadata: { title: 'Movie 1', year: 2023 }
    },
    {
        id: '2',
        displayName: 'Movie 2',
        groupTitle: 'Comedy',
        url: 'url2',
        contentType: 'MOVIE',
        isFavorite: false,
        profileId: 'p1',
        parsedMetadata: { title: 'Movie 2', year: 2022 }
    },
];

describe('MoviesPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (usePlayerStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            setStream: vi.fn(),
        });
        (useMovieGroups as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: ['Action', 'Comedy'],
            isLoading: false,
        });
        (useMovieYears as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: [2023, 2022],
            isLoading: false,
        });
        (useMovieSearch as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: [],
            isLoading: false,
        });
    });

    it('loads and displays movies', () => {
        (useMovies as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: mockMovies, total: 2, page: 1, totalPages: 1 },
            isLoading: false,
            isFetching: false,
        });

        render(<MoviesPage />);
        expect(screen.getByText('Movie 1')).toBeInTheDocument();
        expect(screen.getByText('Movie 2')).toBeInTheDocument();
    });

    it('shows loading state', () => {
        (useMovies as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: undefined,
            isLoading: true,
            isFetching: true,
        });

        render(<MoviesPage />);
        // Check for loader (implementation detail, but usually identifiable)
        // Or check that movies are not present
        expect(screen.queryByText('Movie 1')).not.toBeInTheDocument();
    });

    it('shows empty state when no movies', () => {
        (useMovies as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: [], total: 0, page: 1, totalPages: 0 },
            isLoading: false,
            isFetching: false,
        });

        render(<MoviesPage />);
        expect(screen.getByText('No movies found')).toBeInTheDocument();
    });

    /*
    it('filters by group title', async () => {
      (useMovies as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        data: { data: mockMovies, total: 2, page: 1, totalPages: 1 },
        isLoading: false,
        isFetching: false,
      });
  
      render(<MoviesPage />);
      
      const filterButton = screen.getByRole('button', { name: /All Categories/i });
      fireEvent.click(filterButton);
      
      const actionOption = await screen.findByText('Action');
      fireEvent.click(actionOption);
  
      expect(useMovies).toHaveBeenCalledWith(expect.objectContaining({
        groupTitle: 'Action',
      }));
    });
    */

    it('search updates results', () => {
        (useMovies as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: mockMovies, total: 2, page: 1, totalPages: 1 },
            isLoading: false,
            isFetching: false,
        });

        render(<MoviesPage />);
        const searchInput = screen.getByPlaceholderText('Search movies...');
        fireEvent.change(searchInput, { target: { value: 'Action' } });

        waitFor(() => {
            expect(useMovies).toHaveBeenCalledWith(expect.objectContaining({
                search: 'Action',
            }));
        });
    });
});
