import { Outlet, useLocation, Navigate } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import VideoPlayer from '../player/VideoPlayer';
import { useProfileStore } from '../../store/profileStore';
import { useEffect, useState } from 'react';
import { profilesService } from '../../services/profiles.service';

export default function Layout() {
    console.log('Layout.tsx: Rendering');
    const { currentProfile, setCurrentProfile, setProfiles, profiles } = useProfileStore();
    const location = useLocation();

    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadProfiles = async () => {
            try {
                const fetchedProfiles = await profilesService.getAllProfiles();
                setProfiles(fetchedProfiles);

                if (!currentProfile && fetchedProfiles.length > 0) {
                    const activeProfile = fetchedProfiles.find(p => p.isActive) || fetchedProfiles[0];
                    setCurrentProfile(activeProfile);
                }
            } catch (error) {
                console.error('Failed to load profiles:', error);
                setError('Failed to load profiles. Please ensure the backend server is running.');
            } finally {
                setIsLoading(false);
            }
        };

        loadProfiles();
    }, []);

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-screen text-red-500">
                <p className="text-xl font-bold mb-2">Error</p>
                <p>{error}</p>
                <button
                    className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    onClick={() => window.location.reload()}
                >
                    Retry
                </button>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen text-white">
                <p>Loading...</p>
            </div>
        );
    }

    // If no profile is selected
    if (!currentProfile) {
        // If we have no profiles at all, allow access to profiles page to create one
        if (profiles.length === 0) {
            // If not already on profiles page, redirect there
            if (location.pathname !== '/profiles') {
                return <Navigate to="/profiles" replace />;
            }
            // Render just the content (ProfilesPage) without Sidebar/Header
            return (
                <div className="flex h-screen bg-gray-900 text-white">
                    <main className="flex-1 overflow-y-auto p-6">
                        <Outlet />
                    </main>
                </div>
            );
        }

        // If we have profiles but none selected, redirect to profiles page to select one
        if (location.pathname !== '/profiles') {
            return <Navigate to="/profiles" replace />;
        }

        return (
            <div className="flex h-screen bg-gray-900 text-white">
                <main className="flex-1 overflow-y-auto p-6">
                    <Outlet />
                </main>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-gray-900 text-white">
            <Sidebar />
            <div className="flex flex-col flex-1 overflow-hidden">
                <Header />
                <main className="flex-1 overflow-y-auto p-6">
                    <Outlet />
                </main>
            </div>
            <VideoPlayer />
        </div>
    );
}
