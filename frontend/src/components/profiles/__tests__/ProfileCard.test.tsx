import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ProfileCard from '../ProfileCard';
import type { Profile } from '../../../types/profile.types';

const mockProfile: Profile = {
    id: '1',
    name: 'Test Profile',
    isActive: false,
    createdAt: '2023-01-01',
    updatedAt: '2023-01-01',
    stats: {
        totalChannels: 10,
        totalMovies: 5,
        totalSeries: 2,
        totalEpisodes: 20,
        m3uSourcesCount: 1,
    },
};

describe('ProfileCard', () => {
    const onActivate = vi.fn();
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    it('renders profile info', () => {
        render(
            <ProfileCard
                profile={mockProfile}
                isActive={false}
                onActivate={onActivate}
                onEdit={onEdit}
                onDelete={onDelete}
            />
        );
        expect(screen.getByText('Test Profile')).toBeInTheDocument();
        expect(screen.getByText('10')).toBeInTheDocument(); // Channels
    });

    it('shows active state', () => {
        render(
            <ProfileCard
                profile={mockProfile}
                isActive={true}
                onActivate={onActivate}
                onEdit={onEdit}
                onDelete={onDelete}
            />
        );
        expect(screen.getByText('Active Profile')).toBeInTheDocument();
        expect(screen.queryByText('Activate')).not.toBeInTheDocument();
    });

    it('calls handlers', () => {
        render(
            <ProfileCard
                profile={mockProfile}
                isActive={false}
                onActivate={onActivate}
                onEdit={onEdit}
                onDelete={onDelete}
            />
        );

        fireEvent.click(screen.getByText('Activate'));
        expect(onActivate).toHaveBeenCalled();

        fireEvent.click(screen.getByLabelText('Delete profile'));
        expect(onDelete).toHaveBeenCalled();
    });
});
