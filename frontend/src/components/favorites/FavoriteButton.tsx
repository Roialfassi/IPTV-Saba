import { Heart } from 'lucide-react';
import { useFavorite } from '../../hooks/useFavorites';

interface FavoriteButtonProps {
    contentType: 'CHANNEL' | 'MOVIE' | 'SERIES';
    contentId: string;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

export default function FavoriteButton({
    contentType,
    contentId,
    size = 'md',
    className = '',
}: FavoriteButtonProps) {
    const { isFavorite, addFavorite, removeFavorite, isLoading } = useFavorite(
        contentType,
        contentId
    );

    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-5 h-5',
        lg: 'w-6 h-6',
    };

    const handleClick = (e: React.MouseEvent) => {
        e.stopPropagation(); // Prevent card click
        if (isFavorite) {
            removeFavorite();
        } else {
            addFavorite();
        }
    };

    return (
        <button
            onClick={handleClick}
            disabled={isLoading}
            className={`p-2 rounded-full transition-colors ${isFavorite
                    ? 'bg-red-600 hover:bg-red-700'
                    : 'bg-gray-700 hover:bg-gray-600'
                } ${className}`}
            aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
        >
            <Heart
                className={`${sizeClasses[size]} ${isFavorite ? 'fill-current' : ''}`}
            />
        </button>
    );
}
