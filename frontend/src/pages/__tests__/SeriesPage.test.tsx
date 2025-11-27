import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SeriesPage from '../SeriesPage';
import { useSeries } from '../../hooks/useSeries';
import { BrowserRouter } from 'react-router-dom';

// Mock hooks
vi.mock('../../hooks/useSeries', () => ({
    useSeries: vi.fn(),
}));

const mockSeriesList = [
    {
        id: '1',
        name: 'Series 1',
        normalizedName: 'series-1',
        totalEpisodes: 10,
        totalSeasons: 1,
        profileId: 'p1'
    },
    {
        id: '2',
        name: 'Series 2',
        normalizedName: 'series-2',
        totalEpisodes: 20,
        totalSeasons: 2,
        profileId: 'p1'
    },
];

const renderWithRouter = (component: React.ReactNode) => {
    return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('SeriesPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('loads and displays series', () => {
        (useSeries as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: mockSeriesList, total: 2, page: 1, totalPages: 1 },
            isLoading: false,
            isFetching: false,
        });

        renderWithRouter(<SeriesPage />);
        expect(screen.getByText('Series 1')).toBeInTheDocument();
        expect(screen.getByText('Series 2')).toBeInTheDocument();
    });

    it('shows loading state', () => {
        (useSeries as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: undefined,
            isLoading: true,
            isFetching: true,
        });

        renderWithRouter(<SeriesPage />);
        // Check for loader or absence of series
        expect(screen.queryByText('Series 1')).not.toBeInTheDocument();
    });

    it('shows empty state when no series', () => {
        (useSeries as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: [], total: 0, page: 1, totalPages: 0 },
            isLoading: false,
            isFetching: false,
        });

        renderWithRouter(<SeriesPage />);
        expect(screen.getByText('No series found')).toBeInTheDocument();
    });

    it('search updates results', () => {
        (useSeries as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
            data: { data: mockSeriesList, total: 2, page: 1, totalPages: 1 },
            isLoading: false,
            isFetching: false,
        });

        renderWithRouter(<SeriesPage />);
        const searchInput = screen.getByPlaceholderText('Search series...');
        fireEvent.change(searchInput, { target: { value: 'Series 1' } });

        waitFor(() => {
            expect(useSeries).toHaveBeenCalledWith(expect.objectContaining({
                search: 'Series 1',
            }));
        });
    });
});
