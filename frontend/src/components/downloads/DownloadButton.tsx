import { useState } from 'react';
import { Download, Loader, Check, X } from 'lucide-react';
import { useDownload } from '../../hooks/useDownloads';

interface DownloadButtonProps {
    contentType: 'MOVIE' | 'EPISODE';
    contentId: string;
    title: string;
    url: string;
    logo?: string;
    // For episodes
    seriesId?: string;
    seriesName?: string;
    seasonNumber?: number;
    episodeNumber?: number;
}

export default function DownloadButton(props: DownloadButtonProps) {
    const { queueDownload, isDownloading, isDownloaded, progress } = useDownload(
        props.contentType,
        props.contentId
    );

    const handleDownload = async () => {
        try {
            await queueDownload(props);
        } catch (error: any) {
            alert(error.message || 'Download failed');
        }
    };

    if (isDownloaded) {
        return (
            <button
                className="p-2 bg-green-600 rounded-full"
                disabled
                aria-label="Downloaded"
            >
                <Check className="w-5 h-5" />
            </button>
        );
    }

    if (isDownloading) {
        return (
            <div className="relative p-2">
                <svg className="w-5 h-5 transform -rotate-90">
                    <circle
                        cx="10"
                        cy="10"
                        r="8"
                        stroke="currentColor"
                        strokeWidth="2"
                        fill="none"
                        className="text-gray-700"
                    />
                    <circle
                        cx="10"
                        cy="10"
                        r="8"
                        stroke="currentColor"
                        strokeWidth="2"
                        fill="none"
                        strokeDasharray={`${2 * Math.PI * 8}`}
                        strokeDashoffset={`${2 * Math.PI * 8 * (1 - progress / 100)}`}
                        className="text-blue-500"
                    />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold">
                    {Math.round(progress)}
                </span>
            </div>
        );
    }

    return (
        <button
            onClick={handleDownload}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-full transition-colors"
            aria-label="Download"
        >
            <Download className="w-5 h-5" />
        </button>
    );
}
