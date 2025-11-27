import { useState, useEffect } from 'react';
import { useSettings, useUpdateSettings } from '../../hooks/useSettings';
import { Play, Volume2 } from 'lucide-react';

export default function PlaybackSettings() {
    const { data: settings } = useSettings();
    const updateSettings = useUpdateSettings();

    const [formData, setFormData] = useState({
        autoplay: true,
        defaultQuality: 'auto',
        defaultVolume: 80,
        skipIntroSeconds: 0,
        subtitlesEnabled: false,
        subtitlesLanguage: 'en',
    });

    useEffect(() => {
        if (settings) {
            setFormData({
                autoplay: settings.autoplay,
                defaultQuality: settings.defaultQuality,
                defaultVolume: settings.defaultVolume,
                skipIntroSeconds: settings.skipIntroSeconds,
                subtitlesEnabled: settings.subtitlesEnabled,
                subtitlesLanguage: settings.subtitlesLanguage,
            });
        }
    }, [settings]);

    const handleSave = async () => {
        await updateSettings.mutateAsync(formData);
        alert('Playback settings saved!');
    };

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold mb-4 text-white">Playback Settings</h2>
            </div>

            <div className="space-y-4 bg-gray-800 rounded-lg p-6">
                {/* Autoplay */}
                <div className="flex items-center justify-between">
                    <div>
                        <label className="block text-sm font-medium text-gray-300">
                            Autoplay Next Episode
                        </label>
                        <p className="text-xs text-gray-400 mt-1">
                            Automatically play the next episode in a series
                        </p>
                    </div>
                    <input
                        type="checkbox"
                        checked={formData.autoplay}
                        onChange={(e) => setFormData(prev => ({ ...prev, autoplay: e.target.checked }))}
                        className="w-5 h-5 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                    />
                </div>

                {/* Default Quality */}
                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Default Video Quality
                    </label>
                    <select
                        value={formData.defaultQuality}
                        onChange={(e) => setFormData(prev => ({ ...prev, defaultQuality: e.target.value }))}
                        className="w-full px-4 py-2 bg-gray-700 rounded-lg text-white border border-gray-600 focus:ring-blue-500"
                    >
                        <option value="auto">Auto</option>
                        <option value="1080p">1080p</option>
                        <option value="720p">720p</option>
                        <option value="480p">480p</option>
                    </select>
                </div>

                {/* Default Volume */}
                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Default Volume: {formData.defaultVolume}%
                    </label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={formData.defaultVolume}
                        onChange={(e) => setFormData(prev => ({ ...prev, defaultVolume: parseInt(e.target.value) }))}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                    />
                </div>

                {/* Skip Intro */}
                <div>
                    <label className="block text-sm font-medium mb-2 text-gray-300">
                        Auto-Skip Intro (seconds)
                    </label>
                    <input
                        type="number"
                        min="0"
                        max="300"
                        value={formData.skipIntroSeconds}
                        onChange={(e) => setFormData(prev => ({ ...prev, skipIntroSeconds: parseInt(e.target.value) }))}
                        className="w-full px-4 py-2 bg-gray-700 rounded-lg text-white border border-gray-600 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                        0 = disabled. Skip intro automatically after this many seconds.
                    </p>
                </div>
            </div>

            <button
                onClick={handleSave}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white"
            >
                Save Changes
            </button>
        </div>
    );
}
