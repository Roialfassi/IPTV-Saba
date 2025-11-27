import { useState } from 'react';
import { useProfiles, useProfile, useCreateProfile, useSetActiveProfile, useDeleteProfile, useAddM3USource, useRemoveM3USource, useSyncM3USource } from '../hooks/useProfiles';
import { useProfileStore } from '../store/profileStore';
import ProfileCard from '../components/profiles/ProfileCard';
import M3USourceForm from '../components/profiles/M3USourceForm';
import CreateProfileModal from '../components/profiles/CreateProfileModal';
import SyncStatus from '../components/profiles/SyncStatus';
import { Plus, Loader } from 'lucide-react';

export default function ProfilesPage() {
    const [showAddSource, setShowAddSource] = useState<string | null>(null);
    const [showCreateProfile, setShowCreateProfile] = useState(false);
    const { currentProfile: storedProfile } = useProfileStore();

    // Calculate polling interval: if any source is syncing, poll every 2s
    const shouldPoll = storedProfile?.m3uSources?.some(s =>
        s.lastStatus === 'FETCHING' || s.lastStatus === 'PARSING'
    );

    const { data: activeProfile } = useProfile(storedProfile?.id || '', shouldPoll ? 2000 : undefined);
    const currentProfile = activeProfile || storedProfile;

    const { data: profiles, isLoading } = useProfiles();
    const createProfile = useCreateProfile();
    const setActive = useSetActiveProfile();
    const deleteProfile = useDeleteProfile();
    const addM3USource = useAddM3USource();
    const removeM3USource = useRemoveM3USource();
    const syncM3USource = useSyncM3USource();

    const handleCreateProfile = async (name: string) => {
        try {
            await createProfile.mutateAsync({ name });
            setShowCreateProfile(false);
        } catch (error) {
            console.error('Failed to create profile:', error);
            alert('Failed to create profile');
        }
    };

    const handleDeleteProfile = (id: string) => {
        if (confirm('Are you sure you want to delete this profile? All content will be removed.')) {
            deleteProfile.mutate(id);
        }
    };

    const handleAddSource = async (profileId: string, url: string, name?: string) => {
        try {
            await addM3USource.mutateAsync({ profileId, url, name });
            setShowAddSource(null);
            alert('M3U source added! Sync will start automatically.');
        } catch (error: any) {
            alert(error.response?.data?.message || 'Failed to add M3U source');
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-20">
                <Loader className="w-8 h-8 animate-spin text-blue-500" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-white">Profiles</h1>
                <button
                    onClick={() => setShowCreateProfile(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    Create Profile
                </button>
            </div>

            {/* Profiles Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {profiles?.map((profile) => (
                    <ProfileCard
                        key={profile.id}
                        profile={profile}
                        isActive={currentProfile?.id === profile.id}
                        onActivate={() => setActive.mutate(profile.id)}
                        onEdit={() => alert('Edit not implemented yet')}
                        onDelete={() => handleDeleteProfile(profile.id)}
                    />
                ))}
            </div>

            {/* Create Profile Modal */}
            {showCreateProfile && (
                <CreateProfileModal
                    onSubmit={handleCreateProfile}
                    onCancel={() => setShowCreateProfile(false)}
                    isLoading={createProfile.isPending}
                />
            )}

            {/* M3U Sources Section */}
            {currentProfile && (
                <div className="mt-8">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-2xl font-bold text-white">M3U Sources</h2>
                        <button
                            onClick={() => setShowAddSource(currentProfile.id)}
                            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
                        >
                            <Plus className="w-5 h-5" />
                            Add Source
                        </button>
                    </div>

                    {showAddSource === currentProfile.id && (
                        <div className="mb-4">
                            <M3USourceForm
                                onSubmit={(url, name) => handleAddSource(currentProfile.id, url, name)}
                                onCancel={() => setShowAddSource(null)}
                                isLoading={addM3USource.isPending}
                            />
                        </div>
                    )}

                    {currentProfile.m3uSources && currentProfile.m3uSources.length > 0 ? (
                        <div className="space-y-3">
                            {currentProfile.m3uSources.map((source) => (
                                <div key={source.id} className="bg-gray-800 rounded-lg p-4">
                                    <div className="flex items-start justify-between mb-2">
                                        <div className="flex-1">
                                            <h3 className="font-semibold text-white">{source.name || 'Unnamed Source'}</h3>
                                            <p className="text-sm text-gray-400 truncate">{source.url}</p>
                                        </div>
                                        <button
                                            onClick={async () => {
                                                if (confirm('Remove this M3U source?')) {
                                                    try {
                                                        await removeM3USource.mutateAsync({
                                                            profileId: currentProfile.id,
                                                            sourceId: source.id,
                                                        });
                                                    } catch (error: any) {
                                                        console.error('Failed to remove source:', error);
                                                        alert(error.response?.data?.message || 'Failed to remove source');
                                                    }
                                                }
                                            }}
                                            className="text-red-400 hover:text-red-300 text-sm"
                                        >
                                            Remove
                                        </button>
                                    </div>
                                    <SyncStatus
                                        source={source}
                                        onSync={() => syncM3USource.mutate({
                                            profileId: currentProfile.id,
                                            sourceId: source.id,
                                        })}
                                        isSyncing={syncM3USource.isPending}
                                    />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-gray-400 text-center py-8">
                            No M3U sources added yet. Add one to get started!
                        </p>
                    )}
                </div>
            )}
        </div>
    );
}
