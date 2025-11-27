import { useState, useEffect } from 'react';
import { useSettings, useUpdateSettings } from '../../hooks/useSettings';
import { Save, RotateCcw } from 'lucide-react';

export default function GeneralSettings() {
    const { data: settings, isLoading } = useSettings();
    const updateSettings = useUpdateSettings();
    const [hasChanges, setHasChanges] = useState(false);

    const [formData, setFormData] = useState({
        contentLanguage: 'en',
        ageRating: 'all',
        hideAdultContent: false,
    });

    useEffect(() => {
        if (settings) {
            setFormData({
                contentLanguage: settings.contentLanguage,
                ageRating: settings.ageRating,
                hideAdultContent: settings.hideAdultContent,
            });
        }
    }, [settings]);

    const handleChange = (field: string, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        setHasChanges(true);
    };

    const handleSave = async () => {
        try {
            await updateSettings.mutateAsync(formData);
            setHasChanges(false);
            alert('Settings saved successfully!');
        } catch (error) {
            alert('Failed to save settings');
        }
    };

    const handleReset = () => {
        if (settings) {
            setFormData({
                contentLanguage: settings.contentLanguage,
                ageRating: settings.ageRating,
                hideAdultContent: settings.hideAdultContent,
            });
            setHasChanges(false);
        }
    };

    if (isLoading) return <div>Loading...</div>;

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold mb-4 text-white">General Settings</h2>
            </div>

            <div className="space-y-4 bg-gray-800 rounded-lg p-6">
                {/* Content Language */}
                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Content Language
                    </label>
                    <select
                        value={formData.contentLanguage}
                        onChange={(e) => handleChange('contentLanguage', e.target.value)}
                        className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                    >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="it">Italian</option>
                    </select>
                </div>

                {/* Age Rating */}
                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Age Rating Filter
                    </label>
                    <select
                        value={formData.ageRating}
                        onChange={(e) => handleChange('ageRating', e.target.value)}
                        className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                    >
                        <option value="all">All Content</option>
                        <option value="pg">PG and below</option>
                        <option value="pg13">PG-13 and below</option>
                        <option value="r">R and below</option>
                    </select>
                </div>

                {/* Hide Adult Content */}
                <div className="flex items-center justify-between">
                    <div>
                        <label className="block text-sm font-medium text-gray-300">
                            Hide Adult Content
                        </label>
                        <p className="text-xs text-gray-400 mt-1">
                            Filter out adult-rated content from all views
                        </p>
                    </div>
                    <input
                        type="checkbox"
                        checked={formData.hideAdultContent}
                        onChange={(e) => handleChange('hideAdultContent', e.target.checked)}
                        className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                    />
                </div>
            </div>

            {/* Action Buttons */}
            {hasChanges && (
                <div className="flex gap-3">
                    <button
                        onClick={handleSave}
                        disabled={updateSettings.isLoading}
                        className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg transition-colors text-white"
                    >
                        <Save className="w-5 h-5" />
                        Save Changes
                    </button>
                    <button
                        onClick={handleReset}
                        className="flex items-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-white"
                    >
                        <RotateCcw className="w-5 h-5" />
                        Reset
                    </button>
                </div>
            )}
        </div>
    );
}
