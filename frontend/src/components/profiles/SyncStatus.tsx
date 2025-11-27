import type { M3USource } from '../../types/profile.types';
import { RefreshCw, CheckCircle, XCircle, Clock, Loader } from 'lucide-react';

interface SyncStatusProps {
    source: M3USource;
    onSync: () => void;
    isSyncing?: boolean;
}

export default function SyncStatus({ source, onSync, isSyncing }: SyncStatusProps) {
    const getStatusIcon = () => {
        switch (source.lastStatus) {
            case 'SUCCESS':
                return <CheckCircle className="w-5 h-5 text-green-400" />;
            case 'FAILED':
                return <XCircle className="w-5 h-5 text-red-400" />;
            case 'PARSING':
            case 'FETCHING':
                return <Loader className="w-5 h-5 text-blue-400 animate-spin" />;
            default:
                return <Clock className="w-5 h-5 text-gray-400" />;
        }
    };

    const getStatusText = () => {
        switch (source.lastStatus) {
            case 'SUCCESS':
                return `Synced ${source.totalEntries} entries`;
            case 'FAILED':
                return 'Sync failed';
            case 'PARSING':
                return 'Parsing...';
            case 'FETCHING':
                return 'Downloading...';
            default:
                return 'Not synced';
        }
    };

    return (
        <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
                {getStatusIcon()}
                <span className="text-sm text-gray-300">{getStatusText()}</span>
            </div>
            {source.lastFetched && (
                <span className="text-xs text-gray-500">
                    {new Date(source.lastFetched).toLocaleString()}
                </span>
            )}
            <button
                onClick={onSync}
                disabled={isSyncing || source.lastStatus === 'PARSING' || source.lastStatus === 'FETCHING'}
                className="ml-auto p-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                aria-label="Sync source"
            >
                <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
            </button>
        </div>
    );
}
